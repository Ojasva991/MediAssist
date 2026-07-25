"""
Curated first-aid / triage guidance corpus for the RAG layer.

Every `content` string here is written in this project's own words,
summarizing widely-known, standard public first-aid practice (the kind
taught in basic first-aid courses everywhere) - it is NOT copied from
any specific WHO/CDC page or document. That's a deliberate choice, not
an oversight: reproducing another organization's exact wording would be
a copyright problem, and this project has no license to redistribute
WHO/CDC publications verbatim. `source` labels below say "adapted from
general public first-aid guidance" for the same reason - they're a
description of the kind of knowledge this reflects, not a citation of
a specific document.

Scope is deliberately limited to TRIAGE/FIRST-AID ACTIONS (what to do
right now, and how urgently) - never a diagnosis, a treatment plan, or
a medication/dosage recommendation. That mirrors the project's existing
"never diagnose" rule (see app/ai/prompts.py, app/ai/fallback.py) and
the explicit exclusion in this project's roadmap.
"""

from dataclasses import dataclass

_ADAPTED = "Adapted from general public first-aid guidance"


@dataclass(frozen=True)
class GuidanceEntry:
    id: str
    source: str
    topic: str
    keywords: str
    content: str


CORPUS: list[GuidanceEntry] = [
    GuidanceEntry(
        id="chest_pain",
        source=_ADAPTED,
        topic="Chest pain / suspected heart attack",
        keywords=(
            "chest pain pressure squeezing tightness heart attack cardiac arm "
            "jaw shoulder pain sweating nausea"
        ),
        content=(
            "Sudden chest pain, pressure, or tightness - especially alongside "
            "pain spreading to the arm, neck, jaw, or back, sweating, nausea, "
            "or shortness of breath - should be treated as a possible heart "
            "attack. The person should stop all activity, rest sitting up, "
            "and emergency services should be contacted immediately rather "
            "than waiting to see if it passes."
        ),
    ),
    GuidanceEntry(
        id="stroke_fast",
        source=_ADAPTED,
        topic="Stroke warning signs (FAST)",
        keywords=(
            "stroke face drooping arm weakness slurred speech confusion "
            "sudden numbness vision loss balance"
        ),
        content=(
            "Sudden face drooping on one side, arm weakness, slurred or "
            "confused speech, sudden numbness (especially on one side of the "
            "body), sudden vision problems, or sudden loss of balance are "
            "classic stroke warning signs. Treatment is extremely time-"
            "sensitive - emergency services should be called immediately and "
            "the exact time symptoms started should be noted, since it "
            "affects treatment options."
        ),
    ),
    GuidanceEntry(
        id="choking",
        source=_ADAPTED,
        topic="Choking",
        keywords="choking can't breathe coughing gagging airway blocked",
        content=(
            "If someone is choking and can still cough forcefully or speak, "
            "encourage them to keep coughing. If they cannot breathe, speak, "
            "or cough, and are clutching their throat, back blows and "
            "abdominal thrusts (the Heimlich maneuver) are the standard "
            "response, and emergency services should be called if the "
            "airway doesn't clear quickly."
        ),
    ),
    GuidanceEntry(
        id="severe_bleeding",
        source=_ADAPTED,
        topic="Severe or uncontrolled bleeding",
        keywords="severe bleeding uncontrolled blood loss wound cut deep",
        content=(
            "For severe or uncontrolled bleeding, firm, direct pressure "
            "should be applied to the wound with a clean cloth or bandage "
            "without removing it to check, and the area should be elevated "
            "above heart level if possible. Emergency services should be "
            "contacted immediately for bleeding that doesn't slow with "
            "pressure, or that involves a deep wound, a large amount of "
            "blood, or a wound to the chest or abdomen."
        ),
    ),
    GuidanceEntry(
        id="anaphylaxis",
        source=_ADAPTED,
        topic="Severe allergic reaction / anaphylaxis",
        keywords=(
            "severe allergic reaction anaphylaxis swelling throat hives "
            "difficulty breathing allergy epipen"
        ),
        content=(
            "Signs of a severe allergic reaction (anaphylaxis) include rapid "
            "swelling of the face, lips, or throat, hives, difficulty "
            "breathing, or dizziness after exposure to a known allergen "
            "(food, insect sting, medication). This is a medical emergency - "
            "if the person has an epinephrine auto-injector, it should be "
            "used right away, and emergency services should be called even "
            "if symptoms seem to improve afterward."
        ),
    ),
    GuidanceEntry(
        id="seizure",
        source=_ADAPTED,
        topic="Seizure",
        keywords="seizure convulsions shaking unconscious epilepsy jerking",
        content=(
            "During a seizure, the area around the person should be cleared "
            "of anything they could hit, nothing should be placed in their "
            "mouth, and they should not be restrained - they should be "
            "gently turned onto their side once movement stops, to help "
            "keep the airway clear. Emergency services should be called if "
            "the seizure lasts more than 5 minutes, if another follows "
            "shortly after, or if this is the person's first known seizure."
        ),
    ),
    GuidanceEntry(
        id="fever_management",
        source=_ADAPTED,
        topic="Fever",
        keywords="fever high temperature hot chills sweating unwell",
        content=(
            "A fever is a symptom, not an illness by itself, and mild fevers "
            "in otherwise well adults often don't need emergency care. "
            "Medical attention is warranted sooner for a very high or "
            "rapidly rising fever, a fever in an infant, a fever paired with "
            "a stiff neck, confusion, rash, or difficulty breathing, or one "
            "that persists for several days without improvement."
        ),
    ),
    GuidanceEntry(
        id="dehydration",
        source=_ADAPTED,
        topic="Dehydration",
        keywords=(
            "dehydration dizzy dry mouth little urine vomiting diarrhea "
            "thirsty weak"
        ),
        content=(
            "Signs of dehydration include unusual thirst, a dry mouth, "
            "dizziness, dark or infrequent urination, and fatigue. Mild "
            "dehydration is usually managed with small, frequent sips of "
            "water or an oral rehydration solution. Severe signs - "
            "confusion, fainting, very little or no urination, or inability "
            "to keep fluids down - warrant prompt medical attention, "
            "especially in young children or older adults."
        ),
    ),
    GuidanceEntry(
        id="heat_illness",
        source=_ADAPTED,
        topic="Heat exhaustion / heat stroke",
        keywords=(
            "heat exhaustion heat stroke overheating hot weather sweating "
            "confusion high body temperature"
        ),
        content=(
            "Heat exhaustion typically causes heavy sweating, weakness, "
            "nausea, and cool clammy skin, and usually improves by moving to "
            "a cooler place, loosening clothing, and sipping water. Heat "
            "stroke is more serious - hot, dry or flushed skin, confusion, "
            "or loss of consciousness are emergency warning signs, and "
            "emergency services should be called immediately while trying "
            "to cool the person down."
        ),
    ),
    GuidanceEntry(
        id="hypothermia",
        source=_ADAPTED,
        topic="Hypothermia / cold exposure",
        keywords="hypothermia cold exposure shivering confusion cold skin",
        content=(
            "Hypothermia signs include intense shivering, slurred speech, "
            "confusion, and drowsiness after cold exposure. Wet clothing "
            "should be removed and the person warmed gradually with dry "
            "layers and blankets rather than direct high heat. Emergency "
            "services should be contacted for severe shivering that stops "
            "unexpectedly, confusion, or loss of consciousness."
        ),
    ),
    GuidanceEntry(
        id="fracture",
        source=_ADAPTED,
        topic="Suspected broken bone / fracture",
        keywords=(
            "broken bone fracture deformity swelling can't move limb injury"
        ),
        content=(
            "A suspected fracture (visible deformity, inability to bear "
            "weight or move the area, or severe localized pain and swelling "
            "after an injury) should be kept still and supported rather than "
            "straightened, and a cold pack wrapped in cloth can help with "
            "swelling. Medical attention is needed for any suspected "
            "fracture, and it becomes an emergency if the bone is exposed "
            "through the skin or if there's no pulse below the injury."
        ),
    ),
    GuidanceEntry(
        id="sprain_strain",
        source=_ADAPTED,
        topic="Sprain / strain",
        keywords="sprain strain twisted ankle swelling mild joint pain",
        content=(
            "Mild sprains and strains (twisted ankle, pulled muscle) are "
            "commonly managed with rest, ice, gentle compression, and "
            "elevation of the affected area for the first day or two. "
            "Medical evaluation is worth seeking if the person can't bear "
            "any weight at all, the joint looks deformed, or pain and "
            "swelling are severe or not improving after a few days."
        ),
    ),
    GuidanceEntry(
        id="animal_bite",
        source=_ADAPTED,
        topic="Animal or insect bite/sting",
        keywords="animal bite dog bite insect sting snake bite wound",
        content=(
            "For an animal bite, the wound should be washed with soap and "
            "water and covered with a clean bandage, and medical attention "
            "should be sought for any bite that breaks the skin, given the "
            "risk of infection and rabies exposure. A suspected venomous "
            "snake bite is a medical emergency - the limb should be kept "
            "still and lower than the heart, and emergency services should "
            "be contacted right away."
        ),
    ),
    GuidanceEntry(
        id="nosebleed",
        source=_ADAPTED,
        topic="Nosebleed",
        keywords="nosebleed nose bleeding",
        content=(
            "For a typical nosebleed, sitting upright and leaning slightly "
            "forward while pinching the soft part of the nose for about 10 "
            "minutes usually stops the bleeding. Medical attention is "
            "warranted if bleeding doesn't stop after 20 minutes of steady "
            "pressure, if it follows a head injury, or if it's unusually "
            "heavy."
        ),
    ),
    GuidanceEntry(
        id="minor_wound_care",
        source=_ADAPTED,
        topic="Minor cuts and wound care",
        keywords="minor cut small wound scrape graze bleeding stopped",
        content=(
            "Minor cuts and scrapes are typically cleaned with water, "
            "checked for embedded debris, and covered with a clean bandage "
            "after bleeding has been controlled with gentle pressure. "
            "Medical attention is worth seeking if the wound is deep, won't "
            "stop bleeding, shows signs of infection (increasing redness, "
            "warmth, pus, or fever), or was caused by a dirty or rusty "
            "object and the person's tetanus vaccination isn't up to date."
        ),
    ),
    GuidanceEntry(
        id="poisoning",
        source=_ADAPTED,
        topic="Poisoning / accidental ingestion",
        keywords=(
            "poisoning swallowed chemical ingestion overdose accidental "
            "medication"
        ),
        content=(
            "For suspected poisoning or accidental ingestion of a harmful "
            "substance, a poison control center or emergency services should "
            "be contacted immediately, and the container or substance "
            "involved should be kept on hand to describe to responders. "
            "Vomiting should not be induced unless a poison control "
            "professional specifically advises it, since some substances "
            "cause additional harm on the way back up."
        ),
    ),
    GuidanceEntry(
        id="fainting",
        source=_ADAPTED,
        topic="Fainting / loss of consciousness",
        keywords="fainting fainted passed out unconscious unresponsive dizzy",
        content=(
            "If someone faints briefly and quickly regains consciousness, "
            "having them lie down with legs elevated for a few minutes is "
            "usually sufficient. Emergency services should be called if the "
            "person doesn't regain consciousness quickly, is injured from "
            "the fall, has chest pain or an irregular heartbeat, or if "
            "fainting happens repeatedly."
        ),
    ),
    GuidanceEntry(
        id="mental_health_crisis",
        source=_ADAPTED,
        topic="Mental health crisis / suicidal thoughts",
        keywords=(
            "suicidal self harm mental health crisis hopeless overwhelmed "
            "in danger of hurting myself"
        ),
        content=(
            "Thoughts of suicide or self-harm, or an active mental health "
            "crisis, are medical emergencies just as much as a physical one. "
            "The person should not be left alone, and a mental health crisis "
            "line, emergency services, or the nearest emergency department "
            "should be contacted right away. This is a situation for "
            "immediate professional support, not something to try to assess "
            "or manage alone."
        ),
    ),
    GuidanceEntry(
        id="asthma_breathing",
        source=_ADAPTED,
        topic="Asthma attack / breathing difficulty",
        keywords=(
            "asthma attack wheezing difficulty breathing shortness of breath "
            "inhaler tight chest"
        ),
        content=(
            "During an asthma attack, the person should sit upright and use "
            "their prescribed rescue inhaler if they have one. Emergency "
            "services should be contacted if breathing doesn't improve after "
            "using an inhaler, if lips or fingertips look bluish, if the "
            "person can barely speak, or if this is a first-time severe "
            "breathing difficulty with no known inhaler."
        ),
    ),
    GuidanceEntry(
        id="food_poisoning",
        source=_ADAPTED,
        topic="Food poisoning / vomiting and diarrhea",
        keywords=(
            "food poisoning vomiting diarrhea stomach upset nausea "
            "gastroenteritis"
        ),
        content=(
            "Vomiting and diarrhea from suspected food poisoning are usually "
            "managed with rest and small sips of fluid to prevent "
            "dehydration, and symptoms often improve within a day or two. "
            "Medical attention is warranted for high fever, blood in vomit "
            "or stool, signs of significant dehydration, or symptoms that "
            "persist beyond a couple of days."
        ),
    ),
]
