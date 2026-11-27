"""Native A4 commercial-proposal rendering, using only frozen document data."""
from __future__ import annotations

from io import BytesIO
from datetime import datetime, UTC
from functools import lru_cache
import html
import re
from pathlib import Path

import pymupdf
from PIL import Image
from use_cases.company_logo import _content_bbox, CARD_BORDER_COLOR, OUTPUT_SIZE, CONTENT_SIZE

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / 'assets/fonts/proposal'
INK = '#342e29'
MUTED = '#84786d'
PURPLE = '#7e47c4'
RULE = '#e4ded6'
LEFT, RIGHT = 51., 544.


def clean(value):
    return '' if value is None else str(value).strip().replace('\u202f', ' ').replace('\xa0', ' ')


def money(value):
    if value is None or value == '':
        return ''
    return '₪' + f'{round(float(value)):,}'.replace(',', ' ')


@lru_cache(maxsize=12)
def font(name):
    return pymupdf.Font(fontfile=str(FONTS / (name + '.ttf')))


@lru_cache(maxsize=1)
def fallback_font():
    return pymupdf.Font(fontname='cjk')


def _rgb(color):
    return tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))


def logo_image(payload):
    """Remove only the known Profile preview-card frame and empty logo margins."""
    with Image.open(BytesIO(payload)) as source:
        image = source.convert('RGBA')
        if (image.size == (OUTPUT_SIZE,OUTPUT_SIZE)
                and image.getpixel((OUTPUT_SIZE//2,1)) == CARD_BORDER_COLOR
                and image.getpixel((1,OUTPUT_SIZE//2)) == CARD_BORDER_COLOR):
            inset=(OUTPUT_SIZE-CONTENT_SIZE)//2
            image=image.crop((inset,inset,OUTPUT_SIZE-inset,OUTPUT_SIZE-inset))
        image=image.crop(_content_bbox(image))
        output=BytesIO();image.save(output,format='PNG')
        return output.getvalue(), image.size


def preview_image(payload):
    """MuPDF accepts PNG/JPEG; shared Detection crops are stored as WebP."""
    with Image.open(BytesIO(payload)) as image:
        if image.format in {'PNG','JPEG'}:
            return payload
        output = BytesIO()
        image.convert('RGBA' if 'A' in image.getbands() else 'RGB').save(output, format='PNG')
        return output.getvalue()


def _hebrew(value):
    return bool(re.search('[\u0590-\u05ff]', value))


class ProposalDocument:
    def __init__(self, profile, project_name, snapshot, logo_bytes):
        self.doc = pymupdf.open()
        self.profile, self.project, self.snapshot = profile, project_name, snapshot
        self.logo = logo_bytes
        self.fonts = {'body': 'SpaceGrotesk-400', 'medium': 'SpaceGrotesk-500',
                      'mono': 'IBMPlexMono-400', 'boldmono': 'IBMPlexMono-600',
                      'hebrew': 'NotoSansHebrew-400'}
        self.footer_lines = self._footer_lines()
        self.footer_y = 802 - max(4, len(self.footer_lines)) * 12
        self.bottom = min(708, self.footer_y - 24)
        self.new_page()

    def _font_for(self, char, face):
        primary = font(self.fonts[face])
        if primary.has_glyph(ord(char)):
            return self.fonts[face], primary
        fallback = font(self.fonts['hebrew'])
        if fallback.has_glyph(ord(char)):
            return self.fonts['hebrew'], fallback
        # Preserve the pre-existing proposal's non-Latin coverage.
        return 'fallback', fallback_font()

    def width(self, value, size, face='body'):
        return sum(self._font_for(c, face)[1].text_length(c, fontsize=size) for c in value)

    def wrap(self, value, width, size, face='body'):
        result = []
        for paragraph in clean(value).split('\n'):
            line = ''
            for token in re.findall(r'\S+\s*', paragraph):
                if line and self.width((line + token).rstrip(), size, face) > width:
                    result.append(line.rstrip()); line = ''
                for char in token:
                    if line and self.width(line + char, size, face) > width:
                        result.append(line.rstrip()); line = ''
                    line += char
            result.append(line.rstrip())
        return result or ['']

    def text(self, value, x, top, width, size=10, face='body', color=INK, align='left'):
        value = clean(value)
        if not value:
            return 0.
        lines = self.wrap(value, width, size, face)
        lineheight = size * 1.42
        if _hebrew(value):
            first = re.search('[A-Za-z\u0400-\u04ff\u0590-\u05ff]', value)
            direction = 'rtl' if first and _hebrew(first[0]) else 'ltr'
            # Story uses logical sides for RTL; callers specify the physical edge.
            css_align = {'left':'right','right':'left','center':'center'}[align] if direction == 'rtl' else align
            css = ("@font-face{font-family:proposal;src:url(NotoSansHebrew-400.ttf)}"
                   "@font-face{font-family:body;src:url(SpaceGrotesk-400.ttf)}"
                   f'body{{margin:0;padding:0;font-family:proposal,body,sans-serif;font-size:{size}pt;'
                   f'line-height:1.42;color:{color}}}p{{margin:0;text-align:{css_align};direction:{direction}}}')
            height = max(lineheight * len(lines) + 5, lineheight + 5)
            rect = pymupdf.Rect(x, top, x + width, top + height)
            spare, _ = self.page.insert_htmlbox(rect, '<p>' + html.escape(value).replace('\n','<br>') + '</p>',
                                                css=css, archive=pymupdf.Archive(str(FONTS)), scale_low=1)
            if spare < 0:
                raise ValueError('Proposal Hebrew text does not fit its reserved area')
            return height
        for index, line in enumerate(lines):
            tx = x + (width - self.width(line, size, face)) * ({'left':0,'center':.5,'right':1}[align])
            groups = []
            for char in line:
                name, selected = self._font_for(char, face)
                if groups and groups[-1][0] == name:
                    groups[-1][2] += char
                else:
                    groups.append([name, selected, char])
            for name, selected, content in groups:
                self.page.insert_font(fontname=name, fontbuffer=selected.buffer)
                self.page.insert_text((tx, top + size * 1.05 + index * lineheight), content,
                                      fontname=name, fontsize=size, color=_rgb(color))
                tx += selected.text_length(content, fontsize=size)
        return len(lines) * lineheight

    def rule(self, y):
        self.page.draw_line((LEFT,y),(RIGHT,y),color=_rgb(RULE),width=.55)

    def _footer_lines(self):
        p = self.profile
        lines = []
        for key, label in [('company_registration_number','Company No.'),('vat_file_number','VAT File No.')]:
            if clean(p.get(key)): lines.append(label + ' ' + clean(p[key]))
        bank = ' · '.join(label + ': ' + clean(p[key]) for key,label in
                          [('bank_name','Bank'),('bank_number','Bank No.'),('branch_number','Branch'),('account_number','Account')]
                          if clean(p.get(key)))
        if bank: lines.extend(self.wrap(bank, RIGHT-LEFT, 7.4))
        international = ' · '.join(label + ': ' + clean(p[key]) for key,label in [('iban','IBAN'),('swift','SWIFT')]
                                   if clean(p.get(key)))
        if international: lines.extend(self.wrap(international, RIGHT-LEFT, 7.4))
        return lines

    def new_page(self, *, table_header=True):
        self.page = self.doc.new_page(width=595, height=842)
        self.page.draw_rect(self.page.rect, color=None, fill=(1,1,1))
        if self.logo:
            payload, (width,height) = logo_image(self.logo)
            scale = min(161/width,71/height)
            self.page.insert_image(pymupdf.Rect(LEFT,48,LEFT+width*scale,48+height*scale), stream=payload, keep_proportion=True)
        p = self.profile
        street = ' '.join(clean(p.get(k)) for k in ['address_street','address_house_number'] if clean(p.get(k)))
        city = ', '.join(clean(p.get(k)) for k in ['address_city','address_postal_code'] if clean(p.get(k)))
        contacts = [street,city,clean(p.get('address_country')),clean(p.get('public_phone')),
                    clean(p.get('public_email')),clean(p.get('website_url'))]
        y = 51.
        for line in filter(None,contacts):
            y += self.text(line,310,y,RIGHT-310,8.5,color=MUTED,align='right')
        self.header_y = max(148., y + 20)
        self.rule(self.header_y)
        self.y = self.header_y + 24
        self._footer()
        if self.doc.page_count > 1:
            self.y += self.text(self.project,LEFT,self.y,RIGHT-LEFT,15,'mono') + 16
            if table_header:
                self.table_header()

    def _footer(self):
        self.rule(self.footer_y)
        credit_y = self.footer_y + 6
        self.text('estimated with', RIGHT-84,credit_y,84,6.4,color=MUTED,align='right')
        svg = (ROOT / 'assets/brand/costelry_logo_full_cropped.svg').read_bytes()
        with pymupdf.open(stream=svg, filetype='svg') as source:
            with pymupdf.open(stream=source.convert_to_pdf(),filetype='pdf') as brand:
                self.page.show_pdf_page(pymupdf.Rect(RIGHT-72,self.footer_y+18,RIGHT,self.footer_y+32),brand,0,keep_proportion=True)
        y = self.footer_y + 7
        for line in self.footer_lines:
            # Requisites use the left portion first, leaving the brand intact.
            width = 300 if y < self.footer_y + 27 else RIGHT-LEFT
            y += self.text(line,LEFT,y,width,7.4,color=MUTED) if _hebrew(line) else self.text(line,LEFT,y,RIGHT-LEFT,7.4,color=MUTED)

    def ensure(self, height, *, table_header=True):
        if self.y + height > self.bottom:
            self.new_page(table_header=table_header)
        if self.y + height > self.bottom:
            raise ValueError('Proposal block is taller than one page')

    def heading(self, partner, client, date):
        self.text('Commercial Proposal:',LEFT,self.y,360,21.5,'mono')
        self.text('הצעת מחיר',420,self.y,RIGHT-420,18,align='right')
        self.y += 31
        self.y += self.text(self.project or 'Untitled project',LEFT,self.y,RIGHT-LEFT,21.5,'mono')
        for label, value in [('Partner',partner),('Client',client)]:
            if clean(value) and clean(value).lower() not in {'unknown','none','null'}:
                self.y += 4 + self.text(label + ': ' + clean(value),LEFT,self.y+4,RIGHT-LEFT,9,color=MUTED)
        try:
            stamp=datetime.fromisoformat(clean(date).replace('Z','+00:00'))
        except ValueError:
            stamp=datetime.now(UTC)
        self.y += 4
        self.y += self.text('Date: ' + stamp.strftime('%d %B %Y').lstrip('0'),LEFT,self.y,RIGHT-LEFT,8.5,color=MUTED,align='right')
        self.y += 17
        self.table_header()

    def table_header(self):
        for value,x,width,align in [('DESCRIPTION',LEFT,227,'left'),('QTY',286,39,'center'),
                                     ('UNIT PRICE',339,95,'right'),('TOTAL',449,95,'right')]:
            self.text(value,x,self.y,width,8.3,'mono',MUTED,align)
        self.y += 24
        self.rule(self.y)

    def object_row(self, row, image):
        name_lines=self.wrap(clean(row.get('name')) or 'Untitled object',150,12.3,'medium')
        detail_lines=self.wrap(clean(row.get('materials')),150,8.4)
        text_lines=[(v,12.3,'medium',INK) for v in name_lines]+[(v,8.4,'body',MUTED) for v in detail_lines if v]
        first=True
        while text_lines:
            self.ensure(82 if first else 45)
            available=self.bottom-self.y-24
            used=0.; chunk=[]
            while text_lines and used+text_lines[0][1]*1.42 <= available:
                line=text_lines.pop(0);chunk.append(line);used+=line[1]*1.42
            if not chunk:
                raise ValueError('Proposal row cannot fit')
            height=max(80 if first else 35,used+24)
            top=self.y
            if first and image:
                self.page.insert_image(pymupdf.Rect(LEFT+4,top+12,LEFT+62,top+68),stream=preview_image(image),keep_proportion=True)
            if first:
                for value,x,width,align in [(clean(row.get('quantity')),286,39,'center'),
                                            (money(row.get('sale_price_unit')),334,100,'right'),
                                            (money(row.get('sale_price_total')),444,100,'right')]:
                    self.text(value,x,top+29,width,12,'mono',align=align)
            y=top+14
            for value,size,face,color in chunk:
                y+=self.text(value,126,y,150,size,face,color)
            self.y+=height
            self.rule(self.y)
            first=False
            if text_lines:self.new_page()

    def service(self, row):
        self.ensure(42, table_header=False)
        self.text(clean(row.get('name')) or clean(row.get('object_key')).title(),LEFT,self.y+14,350,11)
        self.text(money(row.get('sale_price_unit')),420,self.y+14,124,12,'mono',align='right')
        self.y+=42;self.rule(self.y)

    def totals(self):
        summary=self.snapshot.get('summary') or {}
        advance=self.snapshot.get('advance_payment_percent')
        if advance is not None and (isinstance(advance,bool) or not isinstance(advance,(int,float)) or not float(advance).is_integer() or not 0<=advance<=100):
            raise ValueError('Invalid advance payment percentage')
        days=self.snapshot.get('production_time_working_days')
        terms=[]
        if days is not None:
            if advance is not None and advance>0:
                terms.append(f'Production lead time: {int(days)} working days from receipt of a {int(advance)}% advance payment.')
                terms.append(f'זמן ייצור: {int(days)} ימי עבודה ממועד קבלת מקדמה בשיעור {int(advance)}%.')
            else:
                terms.append(f'Production time: {int(days)} working days after payment')
            terms.append('Delivery and installation excluded')
        if advance is not None:
            terms.append(f'Payment terms: {int(advance)}% advance payment, {100-int(advance)}% on completion')
        terms_height=sum(max(15,len(self.wrap(t,RIGHT-LEFT,8))*12+4) for t in terms)
        self.ensure(107+terms_height, table_header=False)
        self.y+=11
        self.text('Prices in ILS, excluding VAT',LEFT,self.y,RIGHT-LEFT,8,color=MUTED)
        self.y+=28
        vat=summary.get('vat_percent')
        vat_label=f'VAT {vat:g}%' if isinstance(vat,(int,float)) else 'VAT'
        amount_size = min(20., *(width * 20 / max(self.width(money(summary.get(key)), 20, face), 1)
                                 for key,width,face in [('project_price',111,'mono'),('vat',111,'mono'),('total',137,'boldmono')]))
        for title,key,x,width,face,color in [('Project Price','project_price',151,111,'mono',INK),
                                            (vat_label,'vat',280,111,'mono',INK),
                                            ('Project Total','total',407,137,'boldmono',PURPLE)]:
            self.text(title,x,self.y,width,11,'medium',align='right')
            self.text(money(summary.get(key)),x,self.y+26,width,amount_size,face,color,align='right')
        self.y+=68
        for line in terms:
            self.y+=self.text(line,LEFT,self.y,RIGHT-LEFT,8,color=MUTED,align='right')+4

    def finish(self):
        total=len(self.doc)
        for i,page in enumerate(self.doc,1):
            page.insert_text((LEFT,820),f'{i} / {total}',fontsize=7,color=_rgb(MUTED))
        self.doc.subset_fonts()
        data=self.doc.tobytes(garbage=4,deflate=True)
        self.doc.close()
        return data


def render_proposal(*, profile,project_name,partner_name,client_name,snapshot,logo_bytes=None,preview_bytes=None):
    canvas=ProposalDocument(profile,project_name,snapshot,logo_bytes)
    date=(snapshot.get('document') or {}).get('issued_at','')
    canvas.heading(partner_name,client_name,date)
    preview_bytes=preview_bytes or {}
    for row in snapshot.get('rows') or []:
        image=preview_bytes.get(clean(row.get('object_key')))
        canvas.object_row(row,image)
    for row in snapshot.get('project_costs') or []:
        canvas.service(row)
    canvas.totals()
    return canvas.finish()
