import random
import uuid
from collections import Counter
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Восприятие искусства в мультисенсорных музейных форматах",
    page_icon="🖼️",
    layout="centered",
)

st.markdown(
    """
    <style>
    .question-text {
        font-size: 1.06rem;
        line-height: 1.45;
        margin: 0 0 6px 0;
        color: inherit;
        font-weight: 400;
    }

    .hint-text {
        font-size: 0.84rem;
        line-height: 1.35;
        color: rgba(120, 120, 120, 0.95);
        margin: 0 0 10px 0;
    }

    .section-note {
        font-size: 0.98rem;
        line-height: 1.55;
        margin: 0;
    }

    .vpn-banner {
        background: linear-gradient(135deg, #fff1ee 0%, #ffd8d1 100%);
        border: 1px solid rgba(191, 47, 21, 0.28);
        border-left: 7px solid #bf2f15;
        color: #7e1f10;
        padding: 16px 18px;
        border-radius: 14px;
        margin: 8px 0 20px 0;
        font-size: 1.02rem;
        line-height: 1.5;
        font-weight: 600;
    }

    .focus-box {
        background: #fbf1ef;
        border: 1px solid rgba(191, 47, 21, 0.20);
        border-left: 6px solid #bf2f15;
        border-radius: 14px;
        padding: 16px 18px;
        margin: 8px 0 18px 0;
    }

    .focus-box .section-note {
        color: #1f1f1f !important;
    }

    [data-testid="stCaptionContainer"] {
        font-size: 0.92rem !important;
    }

    .block-title {
        font-size: 1rem;
        font-weight: 600;
        margin: 0 0 8px 0;
    }

    .question-gap {
        height: 12px;
    }

    .thanks-box {
        max-width: 760px;
        margin: 40px auto;
        background: #fff3f0;
        border: 1px solid rgba(191, 47, 21, 0.18);
        border-left: 7px solid #bf2f15;
        border-radius: 16px;
        padding: 28px 24px;
    }

    .thanks-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #1f1f1f;
    }

    .thanks-text {
        font-size: 1rem;
        line-height: 1.55;
        color: #1f1f1f;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

VIGNETTE_TARGET_PER_GENDER = 40

LIKERT5_OPTIONS = [
    "Совершенно не согласен(а)",
    "Скорее не согласен(а)",
    "И да, и нет",
    "Скорее согласен(а)",
    "Совершенно согласен(а)",
]

LIKERT7_OPTIONS = [
    "Совершенно не согласен(а)",
    "2",
    "3",
    "4",
    "5",
    "6",
    "Совершенно согласен(а)",
]

UNDERSTANDING_5_OPTIONS = [
    "Совсем не понял(а)",
    "Понял(а) в небольшой степени",
    "Понял(а) частично",
    "Понял(а) в значительной степени",
    "Понял(а) очень хорошо",
]

CULTURE_7_OPTIONS = [
    "Совсем не включен(а)",
    "2",
    "3",
    "4",
    "5",
    "6",
    "Очень включен(а)",
]

ATTITUDE_7_OPTIONS = [
    "Очень отрицательно",
    "2",
    "3",
    "4",
    "5",
    "6",
    "Очень положительно",
]

VIGNETTES = [
    {
        "id": "v1",
        "type": "Постоянная экспозиция",
        "multisensory": "Нет",
        "text": (
            "Представьте, что вы пришли в музей на постоянную экспозицию — "
            "основную часть музейного собрания, которая представлена на постоянной основе.\n\n"
            "Вы входите в зал, где выставлены экспонаты и размещены поясняющие тексты к ним. "
            "Пространство оформлено сдержанно, без дополнительных эффектов. "
            "Основное внимание сосредоточено на самих экспонатах и информации о них."
        ),
    },
    {
        "id": "v2",
        "type": "Постоянная экспозиция",
        "multisensory": "Да",
        "text": (
            "Представьте, что вы пришли в музей на постоянную экспозицию — "
            "основную часть музейного собрания, которая представлена на постоянной основе.\n\n"
            "Вы входите в зал, где выставлены экспонаты и размещены поясняющие тексты к ним. "
            "Помимо этого, в пространстве используются дополнительные элементы взаимодействия "
            "с экспонатами: например, звуковые элементы, запах, световые эффекты или возможность "
            "прикосновения к отдельным материалам и объектам. Эти элементы сопровождают осмотр экспозиции."
        ),
    },
    {
        "id": "v3",
        "type": "Временная выставка",
        "multisensory": "Нет",
        "text": (
            "Представьте, что вы пришли на временную выставку — экспозицию, "
            "которая работает в музее в течение ограниченного времени.\n\n"
            "Вы входите в зал, где выставлены экспонаты и размещены поясняющие тексты к ним. "
            "Пространство оформлено сдержанно, без дополнительных эффектов. "
            "Основное внимание сосредоточено на самих экспонатах и информации о них."
        ),
    },
    {
        "id": "v4",
        "type": "Временная выставка",
        "multisensory": "Да",
        "text": (
            "Представьте, что вы пришли на временную выставку — экспозицию, "
            "которая работает в музее в течение ограниченного времени.\n\n"
            "Вы входите в зал, где выставлены экспонаты и размещены поясняющие тексты к ним. "
            "Помимо этого, в пространстве используются дополнительные элементы взаимодействия "
            "с экспонатами: например, звуковые элементы, запах, световые эффекты или возможность "
            "прикосновения к отдельным материалам и объектам. Эти элементы сопровождают осмотр выставки."
        ),
    },
]

VIGNETTE_ITEMS = [
    ("v_q1_idea", "В такой ситуации для меня было бы важно понять идею или замысел представленных произведений."),
    ("v_q2_return_thought", "Я считаю, что после такого посещения у меня осталась бы мысль или вопрос, к которому хотелось бы возвращаться."),
    ("v_q3_impression_and_understanding", "Мне кажется, что такое посещение дало бы мне не только впечатления, но и понимание увиденного."),
    ("v_q4_not_important_meaning", "В такой ситуации мне было бы не так важно разбираться в смысле отдельных произведений."),
    ("v_q5_main_result_atmosphere", "Мне кажется, что в такой ситуации главным результатом посещения для меня были бы атмосфера и ощущения."),
    ("v_q6_general_feeling", "В такой ситуации для меня было бы важно само общее ощущение от выставки."),
    ("v_q7_general_impression_enough", "В такой ситуации мне было бы достаточно общего впечатления, даже если бы я не стал(а) специально вдумываться в смысл отдельных произведений."),
]

REAL_EXPERIENCE_ITEMS = [
    ("r_q1_emotions", "Главным результатом этого посещения для меня стали сильные впечатления и эмоции."),
    ("r_q2_understand_meaning", "Во время этого посещения для меня было важно понять смысл увиденных произведений."),
    ("r_q3_followed_flow", "Во время этого посещения я скорее следовал(а) общему потоку людей, чем выстраивал(а) собственный маршрут."),
    ("r_q4_read_labels", "Во время этого посещения я регулярно обращался(ась) к подписям и поясняющим текстам."),
    ("r_q5_overloaded_senses", "Пространство этой экспозиции казалось мне слишком перегружающим мои органы чувств."),
    ("r_q6_focus_despite_effects", "Во время этого посещения мне удавалось удерживать внимание на главном, несмотря на дополнительные эффекты взаимодействия с экспонатами."),
    ("r_q7_sensations_more_than_content", "Во время этого посещения я в большей степени фокусировался(ась) на ощущениях, чем на содержании произведений."),
    ("r_q8_personal_reflection", "После этого посещения у меня возникли размышления о чем-то важном для меня."),
    ("r_q9_important_not_distracted", "Во время этого посещения для меня было важно спокойно рассматривать произведения, не отвлекаясь на внешние стимулы."),
    ("r_q10_effects_helped_understanding", "В этом посещении дополнительные элементы взаимодействия с экспонатами помогали мне лучше понять произведения, а не отвлекали от них."),
    ("r_q11_entertainment_more_than_learning", "Это посещение воспринималось мной скорее как развлечение, чем как познавательный опыт."),
    ("r_q12_related_to_knowledge", "Во время этого посещения я соотносил(а) увиденное со своими знаниями об искусстве, истории или культуре."),
    ("r_q13_immersion_important", "Во время этого посещения для меня было важно переживание погружения в пространство экспозиции."),
    ("r_q14_spectacle_more_than_art", "В этом формате, как мне показалось, зрелищность была важнее самих произведений искусства."),
    ("r_q15_space_distance_scale", "Во время этого посещения для меня были важны движение по пространству, дистанция до экспонатов, масштаб и расположение работ в зале."),
    ("r_q16_lacked_explanations", "Во время этого посещения мне не хватало пояснений и смысловой рамки."),
    ("r_q17_sequence_of_effects", "Во время этого посещения экспозиция воспринималась мной скорее как последовательность эффектов, чем как целостное знакомство с произведениями."),
    ("r_q18_personal_growth", "Для меня важным итогом этого посещения было ощущение личного роста или внутреннего развития."),
    ("r_q19_addressed_to_people_like_me", "Этот формат посещения воспринимался мной как адресованный таким посетителям, как я."),
    ("r_q20_body_included", "Во время этого посещения я ощущал(а) включенность собственного тела в музейный опыт, а не только зрительное восприятие."),
    ("r_q21_more_effects_desired", "Мне хотелось бы, чтобы в таком формате было больше эффектов и более интенсивное вовлечение."),
    ("r_q22_touch_increases_engagement", "Возможность тактильного или физического взаимодействия с экспозицией усиливает для меня вовлеченность."),
]


def scroll_to_top():
    st.markdown(
        """
        <script>
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;

        setTimeout(() => {
            window.scrollTo(0, 0);
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
        }, 50);

        setTimeout(() => {
            window.scrollTo(0, 0);
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
        }, 150);
        </script>
        """,
        unsafe_allow_html=True,
    )


def connect_spreadsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    return client.open("survey_data")


def get_or_create_worksheet(spreadsheet, title: str, rows: int = 1000, cols: int = 100):
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)


def ensure_headers(ws, headers):
    existing = ws.row_values(1)
    if not existing:
        ws.append_row(headers)

def log_failed_screening(
    screening_ws,
    gender,
    age,
    moscow_resident,
    visited_multisensory_last_12m,
    consent,
):
    fail_age = not (18 <= int(age) <= 34)
    fail_moscow = moscow_resident == "Нет"
    fail_multisensory = visited_multisensory_last_12m == "Нет"
    fail_consent = consent == "Нет"

    fail_reasons = []
    if fail_age:
        fail_reasons.append("Возраст не 18–34")
    if fail_moscow:
        fail_reasons.append("Не проживает в Москве")
    if fail_multisensory:
        fail_reasons.append("Не был(а) в подходящем музее/выставке за 12 месяцев")
    if fail_consent:
        fail_reasons.append("Нет согласия")

    screening_ws.append_row([
        datetime.now().isoformat(),
        str(uuid.uuid4()),
        gender,
        int(age),
        moscow_resident,
        visited_multisensory_last_12m,
        consent,
        "Да" if fail_age else "Нет",
        "Да" if fail_moscow else "Нет",
        "Да" if fail_multisensory else "Нет",
        "Да" if fail_consent else "Нет",
        "; ".join(fail_reasons),
    ])


def init_sheets(spreadsheet):
    responses_ws = get_or_create_worksheet(spreadsheet, "responses", rows=5000, cols=150)
    dashboard_ws = get_or_create_worksheet(spreadsheet, "dashboard", rows=200, cols=20)
    screening_ws = get_or_create_worksheet(spreadsheet, "screening_failures", rows=5000, cols=30)

    response_headers = [
        "timestamp",
        "response_id",
        "opened_at",
        "screening_passed_at",
        "submitted_at",
        "seconds_to_screening",
        "seconds_after_screening",
        "seconds_total",
        "gender",
        "age",
        "moscow_resident",
        "visited_multisensory_last_12m",
        "consent",
        "vignette_id",
        "vignette_type",
        "vignette_multisensory",
        "vignette_open_first_action",
        "v_q1_idea",
        "v_q2_return_thought",
        "v_q3_impression_and_understanding",
        "v_q4_not_important_meaning",
        "v_q5_main_result_atmosphere",
        "v_q6_general_feeling",
        "v_q7_general_impression_enough",
        "real_visit_type",
        "real_visit_when",
        "real_visit_with_whom",
        "effect_sound",
        "effect_smell",
        "effect_touch",
        "effect_light",
        "effect_other_selected",
        "real_visit_main_thing",
        "r_q1_emotions",
        "r_q2_understand_meaning",
        "r_q3_followed_flow",
        "r_q4_read_labels",
        "r_q5_overloaded_senses",
        "r_q6_focus_despite_effects",
        "r_q7_sensations_more_than_content",
        "r_q8_personal_reflection",
        "r_q9_important_not_distracted",
        "r_q10_effects_helped_understanding",
        "r_q11_entertainment_more_than_learning",
        "r_q12_related_to_knowledge",
        "r_q13_immersion_important",
        "r_q14_spectacle_more_than_art",
        "r_q15_space_distance_scale",
        "r_q16_lacked_explanations",
        "r_q17_sequence_of_effects",
        "r_q18_personal_growth",
        "r_q19_addressed_to_people_like_me",
        "r_q20_body_included",
        "r_q21_more_effects_desired",
        "r_q22_touch_increases_engagement",
        "understood_authors_intent",
        "museum_frequency",
        "other_culture_frequency",
        "cultural_inclusion",
        "multisensory_visits_12m",
        "general_attitude_multisensory",
        "usual_social_format",
        "visit_alone_frequency",
        "visit_with_others_frequency",
        "education",
        "personal_financial_status",
    ]
    
    screening_headers = [
        "timestamp",
        "screening_id",
        "gender",
        "age",
        "moscow_resident",
        "visited_multisensory_last_12m",
        "consent",
        "fail_age",
        "fail_moscow",
        "fail_multisensory",
        "fail_consent",
        "fail_reasons",
    ]

    ensure_headers(responses_ws, response_headers)
    ensure_headers(screening_ws, screening_headers)
    return responses_ws, dashboard_ws, screening_ws


def reset_survey():
    keys_to_clear = [
        "screening_done",
        "screening_passed",
        "screening_gender",
        "screening_age",
        "screening_moscow",
        "screening_multisensory",
        "screening_consent",
        "assigned_vignette",
        "survey_submitted",
        "vignette_item_order",
        "real_experience_item_order",
        "scroll_top_on_render",
        "opened_at",
        "screening_passed_at",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def question_gap():
    st.markdown("<div class='question-gap'></div>", unsafe_allow_html=True)


def question_text(text: str):
    st.markdown(f"<div class='question-text'>{text}</div>", unsafe_allow_html=True)


def hint_text(text: str):
    st.markdown(f"<div class='hint-text'>{text}</div>", unsafe_allow_html=True)


def radio_one(label: str, options, key: str):
    question_text(label)
    hint_text("Выберите один ответ.")
    value = st.radio(
        " ",
        options,
        index=None,
        key=key,
        label_visibility="collapsed",
    )
    question_gap()
    return value


def number_input_one(label: str, key: str, min_value: int, max_value: int, placeholder: str):
    question_text(label)
    hint_text("Введите ответ.")
    value = st.number_input(
        " ",
        min_value=min_value,
        max_value=max_value,
        step=1,
        value=None,
        placeholder=placeholder,
        key=key,
        label_visibility="collapsed",
    )
    question_gap()
    return value


def text_area_one(label: str, key: str):
    question_text(label)
    hint_text("Введите ответ.")
    value = st.text_area(
        " ",
        key=key,
        label_visibility="collapsed",
    )
    question_gap()
    return value


def checkbox_group(label: str):
    question_text(label)
    hint_text("Выберите несколько вариантов.")


def scale_5(label: str, key: str, show_hint: bool = False):
    question_text(label)
    if show_hint:
        hint_text("Выберите один ответ.")
    value = st.select_slider(
        " ",
        options=LIKERT5_OPTIONS,
        value=None,
        key=key,
        label_visibility="collapsed",
    )
    question_gap()
    return value


def scale_7(label: str, key: str, show_hint: bool = False):
    question_text(label)
    if show_hint:
        hint_text("Выберите один ответ.")
    value = st.select_slider(
        " ",
        options=LIKERT7_OPTIONS,
        value=None,
        key=key,
        label_visibility="collapsed",
    )
    question_gap()
    return value


def single_slider(label: str, options, key: str, show_hint: bool = False):
    question_text(label)
    if show_hint:
        hint_text("Выберите один ответ.")
    value = st.select_slider(
        " ",
        options=options,
        value=None,
        key=key,
        label_visibility="collapsed",
    )
    question_gap()
    return value


def read_completed_rows(ws):
    records = ws.get_all_records()
    return [r for r in records if str(r.get("response_id", "")).strip()]


def compute_counts(records):
    vignette_counts = Counter()
    vignette_gender_counts = Counter()
    gender_counts = Counter()
    age_counts = Counter()

    for record in records:
        vignette_id = str(record.get("vignette_id", "")).strip()
        gender = str(record.get("gender", "")).strip()
        age = str(record.get("age", "")).strip()

        if vignette_id:
            vignette_counts[vignette_id] += 1
        if vignette_id and gender:
            vignette_gender_counts[(vignette_id, gender)] += 1
        if gender:
            gender_counts[gender] += 1
        if age:
            age_counts[age] += 1

    return vignette_counts, vignette_gender_counts, gender_counts, age_counts


def choose_vignette_least_filled(records, gender):
    _, vignette_gender_counts, _, _ = compute_counts(records)

    candidates = []
    min_ratio = None

    for vignette in VIGNETTES:
        count = vignette_gender_counts.get((vignette["id"], gender), 0)
        ratio = count / VIGNETTE_TARGET_PER_GENDER

        if min_ratio is None or ratio < min_ratio:
            min_ratio = ratio
            candidates = [vignette]
        elif ratio == min_ratio:
            candidates.append(vignette)

    return random.choice(candidates)


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 10**9


def update_dashboard(dashboard_ws, records):
    vignette_counts, vignette_gender_counts, gender_counts, age_counts = compute_counts(records)

    rows = []

    rows.append(["Квоты по виньеткам и полу"])
    rows.append([
        "vignette_id",
        "type",
        "multisensory",
        "gender",
        "count",
        "target",
        "remaining",
        "fill_rate",
    ])

    for vignette in VIGNETTES:
        for gender in ["Женский", "Мужской"]:
            count = vignette_gender_counts.get((vignette["id"], gender), 0)
            remaining = max(VIGNETTE_TARGET_PER_GENDER - count, 0)
            fill_rate = round(count / VIGNETTE_TARGET_PER_GENDER, 3)
            rows.append([
                vignette["id"],
                vignette["type"],
                vignette["multisensory"],
                gender,
                count,
                VIGNETTE_TARGET_PER_GENDER,
                remaining,
                fill_rate,
            ])

    rows.append([])
    rows.append(["Общий счетчик по виньеткам"])
    rows.append(["vignette_id", "count_total"])

    for vignette in VIGNETTES:
        rows.append([
            vignette["id"],
            vignette_counts.get(vignette["id"], 0),
        ])

    rows.append([])
    rows.append(["Счетчик по полу"])
    rows.append(["gender", "count"])
    rows.append(["Женский", gender_counts.get("Женский", 0)])
    rows.append(["Мужской", gender_counts.get("Мужской", 0)])

    for extra_gender, count in gender_counts.items():
        if extra_gender not in {"Женский", "Мужской"}:
            rows.append([extra_gender, count])

    rows.append([])
    rows.append(["Счетчик по возрасту"])
    rows.append(["age", "count"])

    for age in sorted(age_counts.keys(), key=safe_int):
        rows.append([age, age_counts[age]])

    dashboard_ws.clear()
    dashboard_ws.update("A1", rows)


try:
    spreadsheet = connect_spreadsheet()
    responses_ws, dashboard_ws, screening_ws = init_sheets(spreadsheet)
    existing_records = read_completed_rows(responses_ws)
    update_dashboard(dashboard_ws, existing_records)
except Exception as e:
    st.error("Не удалось подключиться к Google Sheets.")
    st.exception(e)
    st.stop()

if "screening_done" not in st.session_state:
    st.session_state.screening_done = False

if "screening_passed" not in st.session_state:
    st.session_state.screening_passed = False

if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False

if "scroll_top_on_render" not in st.session_state:
    st.session_state.scroll_top_on_render = False

if "opened_at" not in st.session_state:
    st.session_state.opened_at = datetime.now()

if "vignette_item_order" not in st.session_state:
    order = VIGNETTE_ITEMS.copy()
    random.shuffle(order)
    st.session_state.vignette_item_order = order

if "real_experience_item_order" not in st.session_state:
    order = REAL_EXPERIENCE_ITEMS.copy()
    random.shuffle(order)
    st.session_state.real_experience_item_order = order

if st.session_state.scroll_top_on_render:
    scroll_to_top()
    st.session_state.scroll_top_on_render = False

if st.session_state.screening_done and st.session_state.screening_passed:
    if "assigned_vignette" not in st.session_state:
        st.session_state.assigned_vignette = choose_vignette_least_filled(
            existing_records,
            st.session_state.screening_gender,
        )
    vignette = st.session_state.assigned_vignette
else:
    vignette = None

if st.session_state.survey_submitted:
    st.markdown(
        """
        <div class="thanks-box">
            <div class="thanks-title">Спасибо, ваш ответ записан.</div>
            <div class="thanks-text">
                Если вам интересны результаты или вы хотите что-то сказать, пишите в Telegram:
                <b>@mayusikk</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

st.title("Восприятие искусства в мультисенсорных музейных форматах")

st.markdown(
    """
    <div class="vpn-banner">
        Пожалуйста, выключите VPN перед заполнением анкеты. Это ускорит работу анкеты и снизит вероятность сбоев при отправке ответов.
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.screening_done:
    st.write(
        """
Здравствуйте!

Приглашаю вас принять участие в исследовании, посвященном восприятию искусства
в современных музейных и выставочных форматах.

Опрос анонимный и займет около 12–15 минут.

Вопросы касаются впечатлений, восприятия и оценки музейного опыта.
Пожалуйста, отвечайте внимательно и последовательно, опираясь на свое мнение и опыт.
В анкете нет правильных или неправильных ответов — важна именно ваша личная точка зрения.
"""
    )

if not st.session_state.screening_done:
    with st.container(border=True):
        st.markdown("<div class='block-title'>Сначала несколько вводных вопросов.</div>", unsafe_allow_html=True)

        with st.form("screening_form"):
            gender = radio_one(
                "Укажите ваш пол",
                ["Женский", "Мужской"],
                key="screen_gender",
            )

            age = number_input_one(
                "Сколько вам полных лет?",
                key="screen_age",
                min_value=14,
                max_value=100,
                placeholder="Введите возраст",
            )

            moscow_resident = radio_one(
                "Проживаете ли вы сейчас в Москве на постоянной основе?",
                ["Да", "Нет"],
                key="screen_moscow",
            )

            visited_multisensory_last_12m = radio_one(
                "Были ли вы за последние 12 месяцев в художественном музее или на выставке, где помимо самих экспонатов использовались дополнительные элементы взаимодействия с экспонатами — например, звуковые элементы, запах, возможность касаться, световые эффекты?",
                ["Да", "Нет"],
                key="screen_multisensory",
            )

            consent = radio_one(
                "Согласны ли вы принять участие в исследовании на условиях анонимности и использования ответов только в обобщенном виде в учебных целях?",
                ["Да", "Нет"],
                key="screen_consent",
            )

            screening_submit = st.form_submit_button("Продолжить")

        if screening_submit:
            if (
                gender is None
                or age is None
                or moscow_resident is None
                or visited_multisensory_last_12m is None
                or consent is None
            ):
                st.error("Пожалуйста, заполните все вопросы.")
                st.stop()

            st.session_state.screening_done = True
            st.session_state.screening_gender = gender
            st.session_state.screening_age = int(age)
            st.session_state.screening_moscow = moscow_resident
            st.session_state.screening_multisensory = visited_multisensory_last_12m
            st.session_state.screening_consent = consent

            passed = True
            if not (18 <= int(age) <= 34):
                passed = False
            if moscow_resident == "Нет":
                passed = False
            if visited_multisensory_last_12m == "Нет":
                passed = False
            if consent == "Нет":
                passed = False

            if not passed:
                log_failed_screening(
                    screening_ws=screening_ws,
                    gender=gender,
                    age=age,
                    moscow_resident=moscow_resident,
                    visited_multisensory_last_12m=visited_multisensory_last_12m,
                    consent=consent,
                )

            st.session_state.screening_passed = passed
            if passed:
                st.session_state.screening_passed_at = datetime.now()
            st.session_state.scroll_top_on_render = True
            st.rerun()

    st.stop()

if st.session_state.screening_done and not st.session_state.screening_passed:
    st.warning(
        "Спасибо за интерес к исследованию. "
        "К сожалению, по условиям опроса вы не подходите для дальнейшего участия."
    )
    if st.button("Начать заново"):
        reset_survey()
        st.rerun()
    st.stop()

with st.form("main_survey_form"):
    with st.container(border=True):
        st.markdown("<div class='block-title'>Представьте следующую ситуацию.</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="focus-box">
                <div class="section-note">{vignette["text"].replace(chr(10), "<br>")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        vignette_open_first_action = text_area_one(
            "Оказавшись в такой ситуации, что бы вы, скорее всего, сделали в первую очередь?",
            key="vignette_open_first_action",
        )

        st.write("Пожалуйста, ответьте на следующие вопросы, опираясь именно на описанную ситуацию.\n" \
        "Оцените, пожалуйста, степень своего согласия с суждениями по шкале, где 1 – совершенно не согласен(а), а 5 – совершенно согласен(а).")

        vignette_answers = {}
        for idx, (field_name, field_label) in enumerate(st.session_state.vignette_item_order):
            vignette_answers[field_name] = scale_5(
                field_label,
                key=f"rot_v_{field_name}",
                show_hint=(idx == 0),
            )

    with st.container(border=True):
        st.markdown("<div class='block-title'>Теперь вспомните ваше последнее реальное посещение.</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="focus-box">
                <div class="section-note">
                    Вспомните, пожалуйста, ваше последнее реальное посещение художественного музея или выставки, где помимо самих экспонатов использовались дополнительные элементы взаимодействия с экспонатами — например, звуковые элементы, запах, возможность касаться, световые эффекты.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-note'>Постарайтесь отвечать, опираясь именно на это посещение.</div>",
            unsafe_allow_html=True,
        )

        real_visit_type = radio_one(
            "Что это было?",
            [
                "Постоянная экспозиция",
                "Временная экспозиция",
                "Затрудняюсь ответить",
            ],
            key="real_visit_type",
        )

        real_visit_when = radio_one(
            "Как давно это было?",
            [
                "В последние 2 недели",
                "От 2 недель до 1 месяца назад",
                "От 1 до 3 месяцев назад",
                "От 3 до 6 месяцев назад",
                "От 6 до 12 месяцев назад",
            ],
            key="real_visit_when",
        )

        real_visit_with_whom = radio_one(
            "С кем вы были?",
            [
                "Один(одна)",
                "С партнером",
                "С друзьями",
                "С семьей",
                "Другое",
            ],
            key="real_visit_with_whom",
        )

        checkbox_group("Какие дополнительные эффекты использовались во время данного посещения?")
        effect_sound = st.checkbox("Звуковые элементы", key="effect_sound")
        effect_smell = st.checkbox("Запах", key="effect_smell")
        effect_touch = st.checkbox("Возможность касаться", key="effect_touch")
        effect_light = st.checkbox("Световые эффекты", key="effect_light")
        effect_other_selected = st.checkbox("Другое", key="effect_other_selected")
        question_gap()

        real_visit_main_thing = text_area_one(
            "Что было для вас главным в этом посещении?",
            key="real_visit_main_thing",
        )

        st.write(
            "Ниже приведены высказывания о том посещении, которое вы вспомнили. "
            "Пожалуйста, отметьте, насколько вы согласны с каждым из них. \n"
            "Оцените, пожалуйста, степень своего согласия с суждениями по шкале, где 1 – совершенно не согласен(а), а 7 – совершенно согласен(а)."
        )

        real_experience_answers = {}
        for idx, (field_name, field_label) in enumerate(st.session_state.real_experience_item_order):
            real_experience_answers[field_name] = scale_7(
                field_label,
                key=f"rot_r_{field_name}",
                show_hint=(idx == 0),
            )

        understood_authors_intent = single_slider(
            "Насколько, по вашему мнению, вы поняли замысел произведений на выставке?",
            UNDERSTANDING_5_OPTIONS,
            key="understood_authors_intent",
            show_hint=True,
        )

    with st.container(border=True):
        st.markdown("<div class='block-title'>Теперь несколько вопросов о вашем обычном опыте.</div>", unsafe_allow_html=True)

        museum_frequency = radio_one(
            "Как часто вы обычно посещаете музеи или выставки?",
            [
                "Несколько раз в месяц и чаще",
                "Примерно раз в месяц",
                "Раз в 2–3 месяца",
                "Несколько раз в год",
                "Реже",
                "Затрудняюсь ответить",
            ],
            key="museum_frequency",
        )

        other_culture_frequency = radio_one(
            "Как часто вы посещаете другие культурные события или пространства? (например, театр, концерты, лекции, кинопоказы, фестивали, культурные центры)",
            [
                "Несколько раз в месяц и чаще",
                "Примерно раз в месяц",
                "Раз в 2–3 месяца",
                "Несколько раз в год",
                "Реже",
                "Затрудняюсь ответить",
            ],
            key="other_culture_frequency",
        )

        cultural_inclusion = single_slider(
            "Насколько вы в целом считаете себя включенным(ой) в культурную жизнь?",
            CULTURE_7_OPTIONS,
            key="cultural_inclusion",
            show_hint=True,
        )

        multisensory_visits_12m = radio_one(
            "Сколько раз за последние 12 месяцев вы были в художественном музее или на выставке, где использовались дополнительные элементы взаимодействия с экспонатами — например, звуковые элементы, запах, возможность касаться, световые эффекты или проекции?",
            [
                "1 раз",
                "2–3 раза",
                "4–5 раз",
                "6 раз и более",
                "Затрудняюсь ответить",
            ],
            key="multisensory_visits_12m",
        )

        general_attitude_multisensory = single_slider(
            "Как вы в целом относитесь к форматам художественных музеев и выставок, где помимо самих экспонатов используются дополнительные элементы взаимодействия с экспонатами — например, звуковые элементы, запах, возможность касаться, световые эффекты или проекции?",
            ATTITUDE_7_OPTIONS,
            key="general_attitude_multisensory",
            show_hint=True,
        )

    with st.container(border=True):
        st.markdown("<div class='block-title'>Следующие вопросы посвящены тому, как обычно проходит ваше посещение музеев и выставок.</div>", unsafe_allow_html=True)

        usual_social_format = radio_one(
            "С кем вы чаще всего посещаете музеи или выставки?",
            [
                "Один(одна)",
                "С партнером",
                "С друзьями",
                "С семьей",
                "В составе организованной группы",
            ],
            key="usual_social_format",
        )

        visit_alone_frequency = radio_one(
            "Как часто вы посещаете музеи или выставки в одиночку?",
            ["Почти всегда", "Часто", "Иногда", "Редко", "Никогда"],
            key="visit_alone_frequency",
        )

        visit_with_others_frequency = radio_one(
            "Как часто вы посещаете музеи или выставки с другими людьми?",
            ["Почти всегда", "Часто", "Иногда", "Редко", "Никогда"],
            key="visit_with_others_frequency",
        )

    with st.container(border=True):
        st.markdown("<div class='block-title'>В заключение мы просим вас ответить на несколько вопросов о себе.</div>", unsafe_allow_html=True)

        education = radio_one(
            "Каков ваш уровень образования на сегодняшний день?",
            [
                "Школьное образование (9-11 классов)",
                "Среднее специальное",
                "Незаконченное высшее",
                "Высшее (бакалавриат / специалитет)",
                "Ученая степень (магистр / кандидат, доктор наук)",
            ],
            key="education",
        )

        personal_financial_status = radio_one(
            "Какое из следующих высказываний точнее всего описывает ваше личное материальное положение?",
            [
                "Я едва свожу концы с концами. Денег не хватает даже на продукты.",
                "На продукты денег хватает, но покупка одежды уже вызывает трудности.",
                "Денег хватает на продукты и одежду, но покупка крупной бытовой техники или мебели уже затруднительна.",
                "Я могу без труда покупать бытовую технику и мебель, но покупка автомобиля уже затруднительна.",
                "Я могу без труда купить автомобиль, но покупка квартиры, дачи или другого дорогого имущества уже затруднительна.",
                "Я могу позволить себе практически все, что считаю нужным.",
            ],
            key="personal_financial_status",
        )

    submitted = st.form_submit_button("Отправить")

if submitted:
    required_values = [
        vignette_open_first_action,
        real_visit_type,
        real_visit_when,
        real_visit_with_whom,
        real_visit_main_thing,
        understood_authors_intent,
        museum_frequency,
        other_culture_frequency,
        cultural_inclusion,
        multisensory_visits_12m,
        general_attitude_multisensory,
        usual_social_format,
        visit_alone_frequency,
        visit_with_others_frequency,
        education,
        personal_financial_status,
        *vignette_answers.values(),
        *real_experience_answers.values(),
    ]

    if any(value is None for value in required_values):
        st.error("Пожалуйста, заполните все обязательные вопросы анкеты.")
        st.stop()

    if not vignette_open_first_action.strip():
        st.error("Пожалуйста, ответьте на вопрос о том, что вы сделали бы в первую очередь.")
        st.stop()

    if not real_visit_main_thing.strip():
        st.error("Пожалуйста, ответьте на вопрос о том, что было главным в вашем посещении.")
        st.stop()

    if not any([effect_sound, effect_smell, effect_touch, effect_light, effect_other_selected]):
        st.error("Пожалуйста, укажите хотя бы один дополнительный эффект.")
        st.stop()

    try:
        submitted_at_dt = datetime.now()

        opened_at_dt = st.session_state.get("opened_at")
        screening_passed_at_dt = st.session_state.get("screening_passed_at")

        opened_at_str = opened_at_dt.isoformat() if opened_at_dt else ""
        screening_passed_at_str = screening_passed_at_dt.isoformat() if screening_passed_at_dt else ""
        submitted_at_str = submitted_at_dt.isoformat()

        seconds_to_screening = ""
        seconds_after_screening = ""
        seconds_total = ""

        if opened_at_dt and screening_passed_at_dt:
            seconds_to_screening = round((screening_passed_at_dt - opened_at_dt).total_seconds(), 2)

        if screening_passed_at_dt:
            seconds_after_screening = round((submitted_at_dt - screening_passed_at_dt).total_seconds(), 2)

        if opened_at_dt:
            seconds_total = round((submitted_at_dt - opened_at_dt).total_seconds(), 2)

        row = [
            submitted_at_str,
            str(uuid.uuid4()),
            opened_at_str,
            screening_passed_at_str,
            submitted_at_str,
            seconds_to_screening,
            seconds_after_screening,
            seconds_total,
            st.session_state.screening_gender,
            st.session_state.screening_age,
            st.session_state.screening_moscow,
            st.session_state.screening_multisensory,
            st.session_state.screening_consent,
            vignette["id"],
            vignette["type"],
            vignette["multisensory"],
            vignette_open_first_action.strip(),
            vignette_answers["v_q1_idea"],
            vignette_answers["v_q2_return_thought"],
            vignette_answers["v_q3_impression_and_understanding"],
            vignette_answers["v_q4_not_important_meaning"],
            vignette_answers["v_q5_main_result_atmosphere"],
            vignette_answers["v_q6_general_feeling"],
            vignette_answers["v_q7_general_impression_enough"],
            real_visit_type,
            real_visit_when,
            real_visit_with_whom,
            str(effect_sound),
            str(effect_smell),
            str(effect_touch),
            str(effect_light),
            str(effect_other_selected),
            real_visit_main_thing.strip(),
            real_experience_answers["r_q1_emotions"],
            real_experience_answers["r_q2_understand_meaning"],
            real_experience_answers["r_q3_followed_flow"],
            real_experience_answers["r_q4_read_labels"],
            real_experience_answers["r_q5_overloaded_senses"],
            real_experience_answers["r_q6_focus_despite_effects"],
            real_experience_answers["r_q7_sensations_more_than_content"],
            real_experience_answers["r_q8_personal_reflection"],
            real_experience_answers["r_q9_important_not_distracted"],
            real_experience_answers["r_q10_effects_helped_understanding"],
            real_experience_answers["r_q11_entertainment_more_than_learning"],
            real_experience_answers["r_q12_related_to_knowledge"],
            real_experience_answers["r_q13_immersion_important"],
            real_experience_answers["r_q14_spectacle_more_than_art"],
            real_experience_answers["r_q15_space_distance_scale"],
            real_experience_answers["r_q16_lacked_explanations"],
            real_experience_answers["r_q17_sequence_of_effects"],
            real_experience_answers["r_q18_personal_growth"],
            real_experience_answers["r_q19_addressed_to_people_like_me"],
            real_experience_answers["r_q20_body_included"],
            real_experience_answers["r_q21_more_effects_desired"],
            real_experience_answers["r_q22_touch_increases_engagement"],
            understood_authors_intent,
            museum_frequency,
            other_culture_frequency,
            cultural_inclusion,
            multisensory_visits_12m,
            general_attitude_multisensory,
            usual_social_format,
            visit_alone_frequency,
            visit_with_others_frequency,
            education,
            personal_financial_status,
        ]

        responses_ws.append_row(row)

        updated_records = read_completed_rows(responses_ws)
        update_dashboard(dashboard_ws, updated_records)

        st.session_state.survey_submitted = True
        st.session_state.scroll_top_on_render = True
        st.rerun()

    except Exception as e:
        st.error("Ошибка при записи в таблицу.")
        st.exception(e)