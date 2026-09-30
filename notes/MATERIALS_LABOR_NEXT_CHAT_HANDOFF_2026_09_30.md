# Materials and Labor handoff, 2026-09-30

## Как продолжить

В новом чате сказать: «Продолжаем 3.15.7 по Materials and Labor handoff».

Начинать с этого файла, затем проверить реальный `git status`, текущий HEAD и
тесты. Не начинать с legacy Estimation Agent и не переписывать уже принятые
каталоги без нового доказательства проблемы.

## Текущая цель

Подготовить все детерминированные входы до полной замены Estimation Agent:

```text
source documents
  -> extracted object facts
  -> material identity and price resolution
  -> construction template and production route
  -> labor operations and role hours
  -> company rates, machine cost and overhead
  -> estimate
```

Estimation Agent должен извлекать факты и выбирать только поддерживаемые
сущности. Он не должен придумывать цены, минуты, количество операций или
арифметику.

## Последний проверенный Git checkpoint

- HEAD на момент записи: `a32a921 fix: make price source inputs exclusive`.
- Новый Labor Engine и документы Labor пока не закоммичены.
- Ничего из текущего Labor этапа не отправлялось в production.
- Рабочее дерево грязное и содержит связанные, но разные блоки Materials,
  Price Source, CNC/Laser, purchased components, Labor и ранее начатый
  Estimation scaffold.
- Не удалять и не сбрасывать `.streamlit/`, `tmp/`, SQL catalog parts или
  существующие изменения Price Source и Estimation.

## Архитектура материалов

### Два разных каталожных слоя

1. Global canonical identity catalog отвечает на вопрос: «Что это за
   материал?»
2. Israel pricing identity catalog отвечает на вопрос: «К какому ценовому
   классу он относится и какую стартовую цену можно использовать?»

Это не одна и та же гранулярность. Декор или цвет могут быть важны для
распознавания конкретной позиции, но не обязаны создавать отдельный ценовой
класс.

### Текущие данные

- Новый global catalog SQL содержит 4,436 материалов, 45 категорий и 8,872
  английских и ивритских alias-записей.
- Активный Israel pricing checkpoint содержит 2,832 pricing identities и 2,832
  активные ценовые модели.
- Старые 280 material baselines являются предыдущим фундаментом. Они не должны
  снова становиться основным каталогом вместо global catalog v1.
- В global catalog цена может быть получена из прямого источника или
  детерминированной Israel pricing curve. Метод, confidence и effective date
  хранятся явно.

### Приоритет цены

```text
точная совместимая цена компании
  -> точная Israel pricing identity
  -> review, если scope, единица, VAT, валюта или идентичность несовместимы
```

Компания всегда имеет приоритет. Её supplier row связывается с канонической
identity, но остаётся частной. Общий каталог не должен автоматически обучаться
на частных ценах без будущего агрегирующего и анонимизирующего процесса.

### Resolver и Price Source

- Supplier SKU не является межпоставщицкой идентичностью. Он только
  дополнительный признак внутри одного поставщика.
- Hard attributes, например материал, тип покрытия и толщина, важнее полного
  совпадения названия.
- Цвет, декор и маркетинговое название обычно не меняют ценовой класс.
- Толщина остаётся строгой.
- Неуказанное покрытие у plywood означает raw plywood.
- `white lacquer` для ценовой маршрутизации MDF принято как laminated/faced
  MDF.
- `butcher block` является alias для laminated solid wood panel.
- Если точной связи нет, строка остаётся в частном каталоге компании и получает
  review candidate. Внутреннее слово `shortlist` не должно показываться
  пользователю.
- Operation-service строки, например раскрой, присадка, кромление, доставка и
  монтаж, нельзя сохранять как материалы.
- Resolver failure не должен отменять успешно извлечённый прайс-лист.

### Purchased fabricated components

Работа подрядчика для клиента экономически является покупной позицией:

- subcontractor CNC;
- subcontractor sheet laser;
- изготовленная каменная столешница и её вырезы;
- стекло и акрил в V0;
- другие поставляемые подрядчиком готовые детали.

Для такой строки нельзя одновременно начислять соответствующие внутренние
machine и labor hours. Металлообработка общего назначения пока остаётся Labor
route, а не автоматически purchased component.

### Незавершённое по материалам

1. Estimation пока не потребляет pricing identities.
2. Internal material identity review UI не построен.
3. Нужна production acceptance ещё нескольких реальных источников: URL, PDF,
   XLSX и фотографии.
4. Нужно классифицировать каждый miss как extraction defect, classification
   defect, catalog gap, resolver defect или настоящий review case.
5. Price Source остаётся медленным. Замерять полный пользовательский цикл, а
   не только model time.
6. Нужен multi-stage progress UI или recoverable background workflow.
7. Нужна общая внутренняя система agent failure observability для Source,
   Material Identity, Detection и будущего Estimation.
8. Professional Israel coatings pricing остаётся слабым местом. Не использовать
   иностранный retail или израильский consumer retail как production baseline.
9. Будущее обучение общего рынка на данных компаний требует отдельного решения:
   anonymization, outlier removal, VAT and unit normalization, volume/discount
   separation и минимальная выборка.

## Архитектура Labor

### Принятый pipeline

```text
object facts
  -> validated construction template
  -> primitives
  -> exclusive production route from Company Machinery
  -> operation quantities
  -> setup + rate * quantity
  -> attendance and crew allocation
  -> hours by labor role
```

Labor Engine не считает деньги. Позднее `role hours * company labor rate`
даст labor cost. Machine cost, materials, overhead и margin принадлежат другим
слоям.

### Принятые правила

- Manual, in-house machine и external route взаимно исключаются для одной и
  той же работы.
- Setup начисляется один раз на совместимую производственную партию.
- Machine runtime не равен operator hours. CNC и laser используют attendance
  fraction.
- External component имеет ноль внутреннего производственного labor по той же
  операции.
- Отсутствующие route-critical facts возвращают review, а не выдуманную
  точность.
- Confidence описывает качество baseline, но не скрыто изменяет минуты.
- Физические нормы времени глобальны. Израиль влияет на цены, ставки и внешние
  услуги, но не на физическое время одинаковой операции.
- Exact 16-capability Company Profile Machinery scope защищён. Не добавлять
  Boring machine или новые профильные capabilities без отдельного решения.
- `metal_milling` добавлен как operation identity, а не новая Machinery
  capability.

### Каталоги Labor

- 78 operation identities.
- Роли и физические drivers для каждой операции.
- Baseline формула: `hours = crew * attendance * max(min_batch, setup + rate *
  quantity) / 60`.
- Evidence classes:
  - `R`: source-backed, confidence 60-70;
  - `E`: equipment-bound model, confidence 40;
  - `D`: Costerly derived prior, confidence 25.
- Отдельные metal branches для carbon steel, stainless 304/316, MIG, TIG,
  grinding, polishing, bending, rolling и machining.
- Construction templates для panel furniture, solid wood, metal, glass/stone
  combinations.
- Crew allocation, route catalog, formula catalog и 10 golden scenarios.

Главные документы:

- `notes/LABOR_TIME_BASELINE_V0.md`
- `notes/LABOR_ROUTE_CATALOG_V0.md`
- `notes/LABOR_OPERATION_FORMULAS_V0.md`
- `notes/LABOR_CONSTRUCTION_TEMPLATES_V0.md`
- `notes/LABOR_CREW_ALLOCATION_V0.md`
- `notes/LABOR_GOLDEN_SCENARIOS_V0.md`
- `notes/LABOR_ENGINE_CONTRACT_V0.md`

## Реализованный Labor Engine

Файлы:

- `use_cases/labor_engine.py`
- `tests/test_labor_engine.py`

Сейчас поддерживаются пять template routes:

1. `base_cabinet_open`;
2. `wall_cabinet_hinged`;
3. `vanity_cabinet`;
4. `metal_table_frame`;
5. `sheet_metal_box`.

Реализованы следующие свойства:

- panel saw route без CNC для стандартного прямолинейного корпуса;
- CNC route без одновременного panel saw/manual drilling;
- derivation соединений и отверстий из construction profile;
- carcass, doors, drawers, hardware, packaging, delivery и site labor;
- внешняя каменная столешница без внутренней stone fabrication;
- carbon-steel frame через MIG и внутреннюю powder coating;
- visible stainless frame через TIG, grinding и polishing;
- visible stainless без заявленной finishing qualification уходит в review;
- sheet-metal box может использовать external laser component и internal press
  brake;
- отсутствие размеров, panel route, edge bander или критической квалификации
  возвращает `review_required`;
- каждая labor line хранит operation, route, role hours, baseline version,
  confidence, drivers, formula, batch key и provenance.

Последняя локальная проверка:

- 40 targeted tests passed;
- `git diff --check` passed;
- предупреждение pytest связано только с запретом записи `.pytest_cache` в
  текущем sandbox.

### Важные ограничения текущей реализации

Не называть Labor Engine законченным:

1. Реализованы только 5 из утверждённых templates.
2. S04, S08, S09 и полный S10 ещё не закрыты кодом. S01-S03 и S05-S07 покрыты
   только текущими targeted tests, а не полной production acceptance.
3. Batch aggregation между несколькими объектами отсутствует. Сейчас setup
   может повториться при отдельных вызовах Engine.
4. Panel cut sequence пока прозрачный proxy, а не настоящий cutting-map или
   nesting result.
5. Door and drawer geometry пока не развёрнута в полноценные material
   primitives. Labor для fitting есть, но расход материала требует доработки.
6. `delivery_trip` пока использует один условный trip, а не фактические km и
   traffic class.
7. In-house sheet laser labor и external powder component в sheet-metal
   сценарии ещё не подключены.
8. Не все declared qualified roles проверяются. Жёсткая проверка уже есть для
   visible stainless finishing.
9. Engine не подключён к Price Source, Detection, Estimation runtime, company
   labor rates, overhead или UI.
10. Baseline values класса `D` являются стартовыми priors и требуют будущей
    калибровки на реальных производствах.

## CNC / Laser

- Четыре отдельные экономические модели остаются принятыми: CNC in-house, CNC
  subcontractor, sheet laser in-house, sheet laser subcontractor.
- Отдельного CNC Agent нет и не должно появляться.
- Slider 1-5 относится только к CNC/Laser reserve level. Не распространять его
  на материалы или общий Labor.
- Если CNC доступен in-house, тот же процесс не отправляется subcontractor.
- Если CNC нет, стандартная простая панельная работа может идти через panel saw
  и manual processing. Сложная геометрия идёт subcontractor.
- Ручная резка sheet metal является очень узким исключением. Обычная точная
  листовая деталь идёт через laser.
- Финальное end-to-end тестирование CNC/Laser зависит от нового Estimation
  pipeline, но сами calculators и route rules не следует переписывать вместе с
  Estimation.

## Что делать дальше

Текущая активная задача остаётся 3.15.7.

### P0: закончить Labor Engine

1. Добавить `solid_wood_table` и закрыть golden S04.
2. Добавить `stone_top_on_base` и закрыть S08 с правильным разделением supplier
   fabrication и company installation.
3. Добавить `glass_metal_display` и закрыть S09, включая crew escalation.
4. Закрыть S10 как invariant: installation scope не меняет workshop labor.
5. Добавить остальные approved templates без расширения V0 limits.
6. Добавить batch/session aggregation, чтобы setup считался один раз для
   совместимых объектов.
7. Заменить panel cutting proxy на bounded cutting-map class или другой
   детерминированный источник cut sequences.
8. Завершить role qualification и Machinery guards для каждой route-critical
   операции.
9. Прогнать все 10 golden scenarios и negative/review cases.

### P0 после Labor

1. Зафиксировать Labor Engine checkpoint отдельным commit только после полного
   теста и review diff.
2. Завершить company-first pricing consumption contract.
3. Определить Overhead allocation поверх продуктивных доступных часов компании.
4. Только после этого удалить legacy Estimation Agent и построить Estimation v2
   как bounded fact extraction plus deterministic composition.

### Существующий параллельный backlog

1. 3.15.4 Price Source production acceptance на разных типах источников.
2. 3.15.5 internal material identity review UI.
3. 3.15.6 Price Source speed, progress UX и background recovery.
4. Cross-agent failure observability и internal incident queue.
5. Auth Enter/Forgot Password production acceptance.
6. Local Price Source green-on-green status UI inspection.
7. Professional Israel coatings price evidence.
8. CNC/Laser final production acceptance вместе с новым estimation input.

Эти задачи не отменены переходом к Labor и не должны исчезнуть из очереди.

## Запрещённые короткие пути

- Не подключать legacy Estimation Agent к новым данным «временно».
- Не разрешать LLM возвращать готовые часы или цены.
- Не превращать review в автоматическую связь ради высокого match rate.
- Не создавать отдельную material taxonomy внутри Labor или CNC.
- Не смешивать supplier operation-service и physical material.
- Не смешивать external component с соответствующим внутренним labor.
- Не считать 4,436 material identities как 4,436 независимо подтверждённых
  рыночных цен.
- Не коммитить весь грязный worktree одним общим commit.

## Как проверяем следующий этап

1. Targeted Labor tests.
2. Existing manufacturing routing and costing tests.
3. Все 10 golden scenarios с inspectable trace.
4. Determinism: одинаковые входы дают одинаковый результат.
5. Exclusivity: одна операция имеет только один route.
6. External components дают ноль внутреннего fabrication labor.
7. Missing critical fact даёт конкретный review reason.
8. `git diff --check`.
9. Review только файлов текущей задачи перед отдельным commit.
10. Production/UI acceptance проводить позже, после подключения нового
    Estimation pipeline, в реальной authenticated session.
