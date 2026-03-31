import streamlit as st
from datetime import datetime
import uuid
import random
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Восприятие искусства в мультисенсорных музейных форматах",
    page_icon="🖼️",
    layout="centered",
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

LIKERT5_OPTIONS = [
    "1 — совершенно не согласен(а)",
    "2 — скорее не согласен(а)",
    "3 — и да, и нет",
    "4 — скорее согласен(а)",
    "5 — полностью согласен(а)",
]

VIGNETTES = [
    {
        "id": "v1",
        "type": "Постоянная экспозиция музея",
        "multisensory": "Нет",
        "title": "Постоянная экспозиция музея без мультисенсорного оформления",
        "text": (
            "Представьте, что вы пришли в музей на постоянную экспозицию. "
            "Вы заходите в зал, где представлены экспонаты и размещены поясняющие тексты к ним. "
            "Пространство оформлено сдержанно, без дополнительных эффектов, "
            "и все построено вокруг самих экспонатов."
        ),
    },
    {
        "id": "v2",
        "type": "Постоянная экспозиция музея",
        "multisensory": "Да",
        "title": "Постоянная экспозиция музея с мультисенсорным оформлением",
        "text": (
            "Представьте, что вы пришли в музей на постоянную экспозицию. "
            "Вы заходите в зал, где представлены экспонаты и размещены поясняющие тексты к ним. "
            "Помимо этого, пространство дополнено специальным оформлением, которое делает посещение "
            "более чувственно организованным: в нем используются дополнительные элементы среды и восприятия."
        ),
    },
    {
        "id": "v3",
        "type": "Временная выставка",
        "multisensory": "Нет",
        "title": "Временная выставка без мультисенсорного оформления",
        "text": (
            "Представьте, что вы пришли на временную выставку. "
            "Вы заходите в зал, где представлены экспонаты и размещены поясняющие тексты к ним. "
            "Пространство оформлено сдержанно, без дополнительных эффектов, "
            "и все построено вокруг самих экспонатов."
        ),
    },
    {
        "id": "v4",
        "type": "Временная выставка",
        "multisensory": "Да",
        "title": "Временная выставка с мультисенсорным оформлением",
        "text": (
            "Представьте, что вы пришли на временную выставку. "
            "Вы заходите в зал, где представлены экспонаты и размещены поясняющие тексты к ним. "
            "Помимо этого, пространство дополнено специальным оформлением, которое делает посещение "
            "более чувственно организованным: в нем используются дополнительные элементы среды и восприятия."
        ),
    },
]


def connect_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    return client.open("survey_data").sheet1


def ensure_headers(sheet):
    headers = [
        "timestamp",
        "response_id",
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
        "v_q6_experience_of_space",
        "v_q7_general_impression_enough",
        "real_visit_type",
        "real_visit_when",
        "real_visit_with_whom",
        "r_q1_emotions",
        "r_q2_understand_meaning",
        "r_q3_followed_flow",
        "r_q4_read_labels",
        "r_q5_overloaded",
        "r_q6_focus_despite_effects",
        "r_q7_sensations_more_than_content",
        "r_q8_personal_reflection",
        "r_q9_important_not_distracted",
        "r_q10_effects_helped_understanding",
        "r_q11_entertainment_more_than_learning",
        "r_q12_related_to_knowledge",
        "r_q13_immersion_important",
        "r_q14_spectacle_more_than_art",
        "r_q15_body_space_aspect",
        "r_q16_lacked_explanations",
        "r_q17_sequence_of_effects",
        "r_q18_personal_growth",
        "r_q19_addressed_to_people_like_me",
        "r_q20_body_included",
        "r_q21_more_effects_desired",
        "r_q22_tactile_strengthens",
        "museum_frequency",
        "other_culture_frequency",
        "cultural_inclusion",
        "multisensory_visits_12m",
        "general_attitude_multisensory",
        "usual_social_format",
        "visit_alone_frequency",
        "visit_with_others_frequency",
        "education",
        "family_financial_status",
    ]

    existing = sheet.row_values(1)
    if not existing:
        sheet.append_row(headers)


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
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


try:
    sheet = connect_sheet()
    ensure_headers(sheet)
except Exception as e:
    st.error("Не удалось подключиться к Google Sheets.")
    st.exception(e)
    st.stop()

if "assigned_vignette" not in st.session_state:
    st.session_state.assigned_vignette = random.choice(VIGNETTES)

if "screening_done" not in st.session_state:
    st.session_state.screening_done = False

if "screening_passed" not in st.session_state:
    st.session_state.screening_passed = False

if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False

vignette = st.session_state.assigned_vignette

st.title("Восприятие искусства в мультисенсорных музейных форматах")

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

if st.session_state.survey_submitted:
    st.success("Спасибо! Ваш ответ сохранён.")
    if st.button("Заполнить анкету заново"):
        reset_survey()
        st.rerun()
    st.stop()

# ---------------------------
# БЛОК 1. СКРИНИНГ
# ---------------------------
if not st.session_state.screening_done:
    st.header("Блок 1. Скрининг")

    with st.form("screening_form"):
        gender = st.radio(
            "1. Укажите ваш пол",
            ["Женский", "Мужской"],
            index=None,
        )

        age = st.number_input(
            "2. Сколько вам полных лет?",
            min_value=14,
            max_value=100,
            step=1,
            value=None,
            placeholder="Введите возраст",
        )

        moscow_resident = st.radio(
            "3. Проживаете ли вы сейчас в Москве на постоянной основе?",
            ["Да", "Нет"],
            index=None,
        )

        visited_multisensory_last_12m = st.radio(
            "4. Были ли вы за последние 12 месяцев в музее или на выставке, "
            "где помимо самих экспонатов использовались дополнительные элементы оформления — "
            "например, звук, запах, возможность касаться, световые эффекты, проекции?",
            ["Да", "Нет"],
            index=None,
        )

        consent = st.radio(
            "5. Согласны ли вы принять участие в исследовании на условиях анонимности "
            "и использования ответов только в обобщенном виде в учебных целях?",
            ["Да", "Нет"],
            index=None,
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
            st.error("Пожалуйста, заполните все вопросы скрининга.")
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

        st.session_state.screening_passed = passed
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

# ---------------------------
# ОСНОВНАЯ АНКЕТА
# ---------------------------
st.success("Спасибо! Вы прошли скрининг и можете продолжить заполнение анкеты.")

with st.form("main_survey_form"):
    st.header("Блок 2. Виньетка")

    st.write(
        "Пожалуйста, внимательно прочитайте описание ситуации ниже и представьте, "
        "что вы оказались в таком музее или на такой выставке. "
        "После этого ответьте на несколько вопросов о том, каким, как вам кажется, "
        "был бы ваш опыт в этой ситуации."
    )

    st.subheader(vignette["title"])
    st.write(vignette["text"])

    vignette_open_first_action = st.text_area(
        "6. Оказавшись в такой ситуации, что бы вы, скорее всего, сделали в первую очередь?"
    )

    st.write("Пожалуйста, ответьте на следующие вопросы, опираясь именно на описанную ситуацию.")

    v_q1_idea = st.radio(
        "В такой ситуации для меня было бы важно понять идею или замысел представленных произведений.",
        LIKERT5_OPTIONS,
        index=None,
    )
    v_q2_return_thought = st.radio(
        "Мне кажется, что после такого посещения у меня осталась бы мысль или вопрос, к которому хотелось бы возвращаться.",
        LIKERT5_OPTIONS,
        index=None,
    )
    v_q3_impression_and_understanding = st.radio(
        "Мне кажется, что такое посещение дало бы мне не только впечатления, но и понимание увиденного.",
        LIKERT5_OPTIONS,
        index=None,
    )
    v_q4_not_important_meaning = st.radio(
        "В такой ситуации мне было бы не так важно разбираться в смысле отдельных произведений.",
        LIKERT5_OPTIONS,
        index=None,
    )
    v_q5_main_result_atmosphere = st.radio(
        "Мне кажется, что в такой ситуации главным результатом посещения для меня были бы атмосфера и ощущения.",
        LIKERT5_OPTIONS,
        index=None,
    )
    v_q6_experience_of_space = st.radio(
        "В такой ситуации для меня было бы важно само переживание пространства.",
        LIKERT5_OPTIONS,
        index=None,
    )
    v_q7_general_impression_enough = st.radio(
        "В такой ситуации мне было бы достаточно общего впечатления, даже если бы я не стал(а) специально вдумываться в смысл отдельных произведений.",
        LIKERT5_OPTIONS,
        index=None,
    )

    st.header("Блок 3. Ваш реальный опыт посещения")

    st.write(
        "Теперь вспомните, пожалуйста, ваше последнее реальное посещение музея или выставки, "
        "где помимо самих экспонатов использовались дополнительные элементы оформления — "
        "например, звук, запах, возможность касаться, световые эффекты или проекции."
    )
    st.write("Постарайтесь отвечать, опираясь именно на это посещение.")

    real_visit_type = st.radio(
        "1. Что это было?",
        [
            "Постоянная экспозиция музея",
            "Временная выставка в музее",
            "Временная выставка в отдельном выставочном пространстве",
            "Затрудняюсь ответить",
        ],
        index=None,
    )

    real_visit_when = st.radio(
        "2. Как давно это было?",
        [
            "В последние 2 недели",
            "От 2 недель до 1 месяца назад",
            "От 1 до 3 месяцев назад",
            "От 3 до 6 месяцев назад",
            "От 6 до 12 месяцев назад",
        ],
        index=None,
    )

    real_visit_with_whom = st.radio(
        "3. С кем вы были?",
        [
            "Один(одна)",
            "С партнером",
            "С друзьями",
            "С семьей",
            "В составе организованной группы",
            "Другое",
        ],
        index=None,
    )

    st.write(
        "Ниже приведены высказывания о том посещении, которое вы вспомнили. "
        "Пожалуйста, отметьте, насколько вы согласны с каждым из них."
    )

    r_q1_emotions = st.radio(
        "Главным результатом этого посещения для меня стали сильные впечатления и эмоции.",
        LIKERT5_OPTIONS, index=None
    )
    r_q2_understand_meaning = st.radio(
        "Во время этого посещения для меня было важно понять смысл увиденных произведений.",
        LIKERT5_OPTIONS, index=None
    )
    r_q3_followed_flow = st.radio(
        "Во время этого посещения я скорее следовал(а) общему потоку людей, чем выстраивал(а) собственный маршрут.",
        LIKERT5_OPTIONS, index=None
    )
    r_q4_read_labels = st.radio(
        "Во время этого посещения я регулярно обращался(ась) к подписям и поясняющим текстам.",
        LIKERT5_OPTIONS, index=None
    )
    r_q5_overloaded = st.radio(
        "Пространство этой экспозиции казалось мне перегруженным стимулами.",
        LIKERT5_OPTIONS, index=None
    )
    r_q6_focus_despite_effects = st.radio(
        "Во время этого посещения мне удавалось удерживать внимание на главном, несмотря на дополнительные эффекты оформления.",
        LIKERT5_OPTIONS, index=None
    )
    r_q7_sensations_more_than_content = st.radio(
        "Во время этого посещения я в большей степени фокусировался(ась) на ощущениях, чем на содержании произведений.",
        LIKERT5_OPTIONS, index=None
    )
    r_q8_personal_reflection = st.radio(
        "После этого посещения у меня возникли размышления о чем-то личностно значимом.",
        LIKERT5_OPTIONS, index=None
    )
    r_q9_important_not_distracted = st.radio(
        "Во время этого посещения для меня было важно спокойно рассматривать произведения, не отвлекаясь на внешние стимулы.",
        LIKERT5_OPTIONS, index=None
    )
    r_q10_effects_helped_understanding = st.radio(
        "В этом посещении дополнительные элементы оформления помогали мне лучше понять произведения, а не отвлекали от них.",
        LIKERT5_OPTIONS, index=None
    )
    r_q11_entertainment_more_than_learning = st.radio(
        "Это посещение воспринималось мной скорее как развлечение, чем как познавательный опыт.",
        LIKERT5_OPTIONS, index=None
    )
    r_q12_related_to_knowledge = st.radio(
        "Во время этого посещения я соотносил(а) увиденное со своими знаниями об искусстве, истории или культуре.",
        LIKERT5_OPTIONS, index=None
    )
    r_q13_immersion_important = st.radio(
        "Во время этого посещения для меня было важно переживание погружения в пространство экспозиции.",
        LIKERT5_OPTIONS, index=None
    )
    r_q14_spectacle_more_than_art = st.radio(
        "В этом формате, как мне показалось, зрелищность была важнее самих произведений искусства.",
        LIKERT5_OPTIONS, index=None
    )
    r_q15_body_space_aspect = st.radio(
        "Для меня был значим телесно-пространственный аспект этого посещения — движение, дистанция, масштаб, расположение в пространстве.",
        LIKERT5_OPTIONS, index=None
    )
    r_q16_lacked_explanations = st.radio(
        "Во время этого посещения мне не хватало пояснений и смысловой рамки, а не только эффектной подачи.",
        LIKERT5_OPTIONS, index=None
    )
    r_q17_sequence_of_effects = st.radio(
        "Во время этого посещения экспозиция воспринималась мной скорее как последовательность эффектов, чем как целостное знакомство с произведениями.",
        LIKERT5_OPTIONS, index=None
    )
    r_q18_personal_growth = st.radio(
        "Для меня важным итогом этого посещения было ощущение личного роста или внутреннего развития.",
        LIKERT5_OPTIONS, index=None
    )
    r_q19_addressed_to_people_like_me = st.radio(
        "Этот формат посещения воспринимался мной как адресованный таким посетителям, как я.",
        LIKERT5_OPTIONS, index=None
    )
    r_q20_body_included = st.radio(
        "Во время этого посещения я ощущал(а) включенность собственного тела в музейный опыт, а не только зрительное восприятие.",
        LIKERT5_OPTIONS, index=None
    )
    r_q21_more_effects_desired = st.radio(
        "Мне хотелось бы, чтобы в таком формате было больше эффектов и более интенсивное вовлечение.",
        LIKERT5_OPTIONS, index=None
    )
    r_q22_tactile_strengthens = st.radio(
        "Возможность тактильного или физического взаимодействия с экспозицией усиливает для меня восприятие.",
        LIKERT5_OPTIONS, index=None
    )

    st.header("Блок 4. Ваш опыт посещения музеев и выставок")

    museum_frequency = st.radio(
        "1. Как часто вы обычно посещаете музеи или выставки?",
        [
            "Несколько раз в месяц и чаще",
            "Примерно раз в месяц",
            "Раз в 2–3 месяца",
            "Несколько раз в год",
            "Реже",
            "Затрудняюсь ответить",
        ],
        index=None,
    )

    other_culture_frequency = st.radio(
        "2. Как часто вы посещаете другие культурные события или пространства? "
        "(например, театр, концерты, лекции, кинопоказы, фестивали, культурные центры)",
        [
            "Несколько раз в месяц и чаще",
            "Примерно раз в месяц",
            "Раз в 2–3 месяца",
            "Несколько раз в год",
            "Реже",
            "Затрудняюсь ответить",
        ],
        index=None,
    )

    cultural_inclusion = st.slider(
        "3. Насколько вы в целом считаете себя включенным(ой) в культурную жизнь?",
        min_value=1,
        max_value=7,
        value=4,
        help="1 — совсем не включен(а), 7 — очень включен(а)",
    )

    multisensory_visits_12m = st.radio(
        "4. Сколько раз за последние 12 месяцев вы были в музее или на выставке, где использовались дополнительные элементы оформления — например, звук, запах, возможность касаться, световые эффекты или проекции?",
        [
            "1 раз",
            "2–3 раза",
            "4–5 раз",
            "6 раз и более",
            "Затрудняюсь ответить",
        ],
        index=None,
    )

    general_attitude_multisensory = st.slider(
        "5. Как вы в целом относитесь к форматам музеев и выставок, где помимо самих экспонатов используются дополнительные элементы оформления?",
        min_value=1,
        max_value=7,
        value=4,
        help="1 — очень отрицательно, 7 — очень положительно",
    )

    st.header("Блок 5. Социальный контекст посещения")

    usual_social_format = st.radio(
        "1. Как вы чаще всего посещаете музеи или выставки?",
        [
            "Один(одна)",
            "С партнером",
            "С друзьями",
            "С семьей",
            "В составе организованной группы",
            "По-разному, без одного типичного варианта",
        ],
        index=None,
    )

    visit_alone_frequency = st.radio(
        "2. Как часто вы посещаете музеи или выставки в одиночку?",
        ["Почти всегда", "Часто", "Иногда", "Редко", "Никогда"],
        index=None,
    )

    visit_with_others_frequency = st.radio(
        "3. Как часто вы посещаете музеи или выставки с другими людьми?",
        ["Почти всегда", "Часто", "Иногда", "Редко", "Никогда"],
        index=None,
    )

    st.header("Блок 6. Социально-демографические вопросы")

    education = st.radio(
        "1. Какое у вас образование?",
        [
            "Неполное среднее",
            "Среднее общее",
            "Среднее профессиональное",
            "Неоконченное высшее",
            "Бакалавриат",
            "Специалитет",
            "Магистратура",
            "Аспирантура / ученая степень",
        ],
        index=None,
    )

    family_financial_status = st.radio(
        "2. Какое из следующих высказываний точнее всего описывает материальное положение вашей семьи?",
        [
            "Мы едва сводим концы с концами. Денег не хватает даже на продукты.",
            "На продукты денег хватает, но покупка одежды уже вызывает трудности.",
            "Денег хватает на продукты и одежду, но покупка крупной бытовой техники или мебели уже затруднительна.",
            "Мы можем без труда покупать бытовую технику и мебель, но покупка автомобиля уже затруднительна.",
            "Мы можем без труда купить автомобиль, но покупка квартиры, дачи или другого дорогого имущества уже затруднительна.",
            "Мы можем позволить себе практически все, что считаем нужным.",
        ],
        index=None,
    )

    submitted = st.form_submit_button("Отправить")

if submitted:
    required_fields = [
        vignette_open_first_action,
        v_q1_idea, v_q2_return_thought, v_q3_impression_and_understanding,
        v_q4_not_important_meaning, v_q5_main_result_atmosphere, v_q6_experience_of_space,
        v_q7_general_impression_enough,
        real_visit_type, real_visit_when, real_visit_with_whom,
        r_q1_emotions, r_q2_understand_meaning, r_q3_followed_flow, r_q4_read_labels,
        r_q5_overloaded, r_q6_focus_despite_effects, r_q7_sensations_more_than_content,
        r_q8_personal_reflection, r_q9_important_not_distracted, r_q10_effects_helped_understanding,
        r_q11_entertainment_more_than_learning, r_q12_related_to_knowledge, r_q13_immersion_important,
        r_q14_spectacle_more_than_art, r_q15_body_space_aspect, r_q16_lacked_explanations,
        r_q17_sequence_of_effects, r_q18_personal_growth, r_q19_addressed_to_people_like_me,
        r_q20_body_included, r_q21_more_effects_desired, r_q22_tactile_strengthens,
        museum_frequency, other_culture_frequency, multisensory_visits_12m,
        usual_social_format, visit_alone_frequency, visit_with_others_frequency,
        education, family_financial_status,
    ]

    if any(value is None for value in required_fields) or not vignette_open_first_action.strip():
        st.error("Пожалуйста, заполните все вопросы анкеты.")
        st.stop()

    try:
        row = [
            datetime.now().isoformat(),
            str(uuid.uuid4()),
            st.session_state.screening_gender,
            st.session_state.screening_age,
            st.session_state.screening_moscow,
            st.session_state.screening_multisensory,
            st.session_state.screening_consent,
            vignette["id"],
            vignette["type"],
            vignette["multisensory"],
            vignette_open_first_action.strip(),
            v_q1_idea,
            v_q2_return_thought,
            v_q3_impression_and_understanding,
            v_q4_not_important_meaning,
            v_q5_main_result_atmosphere,
            v_q6_experience_of_space,
            v_q7_general_impression_enough,
            real_visit_type,
            real_visit_when,
            real_visit_with_whom,
            r_q1_emotions,
            r_q2_understand_meaning,
            r_q3_followed_flow,
            r_q4_read_labels,
            r_q5_overloaded,
            r_q6_focus_despite_effects,
            r_q7_sensations_more_than_content,
            r_q8_personal_reflection,
            r_q9_important_not_distracted,
            r_q10_effects_helped_understanding,
            r_q11_entertainment_more_than_learning,
            r_q12_related_to_knowledge,
            r_q13_immersion_important,
            r_q14_spectacle_more_than_art,
            r_q15_body_space_aspect,
            r_q16_lacked_explanations,
            r_q17_sequence_of_effects,
            r_q18_personal_growth,
            r_q19_addressed_to_people_like_me,
            r_q20_body_included,
            r_q21_more_effects_desired,
            r_q22_tactile_strengthens,
            museum_frequency,
            other_culture_frequency,
            cultural_inclusion,
            multisensory_visits_12m,
            general_attitude_multisensory,
            usual_social_format,
            visit_alone_frequency,
            visit_with_others_frequency,
            education,
            family_financial_status,
        ]

        sheet.append_row(row)
        st.session_state.survey_submitted = True
        st.rerun()

    except Exception as e:
        st.error("Ошибка при записи в таблицу.")
        st.exception(e)