from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]


def test_password_recovery_email_uses_public_brand_asset_and_direct_auth_link():
    template = (
        ROOT / "notes/email_templates/password_recovery.html"
    ).read_text(encoding="utf-8")

    assert "https://app.costerly.ai/assets/email/costerly-ai-logo.png" in template
    assert 'alt="Coasterly AI"' in template
    assert "{{ .ConfirmationURL }}" in template
    assert "<svg" not in template
    assert "data:image" not in template
    assert "We received your request. Click the button below to create a new password" in template
    assert "Create a new password for your Coasterly AI account." not in template
    assert "If you didn’t request this, you can safely ignore this email." not in template
    assert ">Reset your password</a>" in template
    assert '<meta name="color-scheme" content="light only">' in template
    assert '<meta name="supported-color-schemes" content="light only">' in template
    assert 'body class="body email-page" bgcolor="#ffffff"' in template
    assert 'class="email-card"' in template
    assert 'bgcolor="#ffffff"' in template
    assert "background-image:linear-gradient(#ffffff,#ffffff)" in template
    assert "border:0;border-radius:0" in template
    assert "#f1efef" not in template
    assert "@media (prefers-color-scheme: dark)" in template
    assert "[data-ogsc] .email-card" in template
    assert "u + .body .gmail-blend-exclusion-black" in template
    assert "u + .body .gmail-blend-difference-black" in template
    assert '<span class="gmail-blend-exclusion-black"><span class="gmail-blend-difference-black">We received your request.' in template


def test_password_recovery_subject_is_unique_without_exposing_the_otp():
    subject = (
        ROOT / "notes/email_templates/password_recovery.subject.txt"
    ).read_text(encoding="utf-8").strip()

    assert subject == "Reset your Coasterly AI password [{{ .TokenHash }}]"
    assert "{{ .Token }}" not in subject


def test_password_recovery_email_logo_is_high_density_transparent_png():
    logo_path = ROOT / "cloudflare/assets/email/costerly-ai-logo.png"

    with Image.open(logo_path) as logo:
        assert logo.size == (806, 154)
        assert logo.mode == "RGBA"
