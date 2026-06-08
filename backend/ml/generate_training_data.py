"""
backend/ml/generate_training_data.py
======================================
PURPOSE:
    Generates synthetic training data for MINDWATCH's three ML classifiers.

    WHY SYNTHETIC DATA?
        Real clinical datasets (DAIC-WOZ, CLPsych, CSSRS) require IRB approval
        and data sharing agreements. For a portfolio project, we generate
        realistic synthetic examples that mirror the linguistic patterns of
        each condition — the models learn the same signal, just from
        synthesized examples instead of real patient data.

    In a production system, you would replace this with:
        - PHQ-9 questionnaire text + score pairs from clinical partners
        - Reddit SuicideWatch dataset (CC BY 4.0, Kaggle)
        - GoEmotions dataset (Apache 2.0, Google Research)

    Run: python backend/ml/generate_training_data.py
"""

import json
import random
import os

random.seed(42)

# ── PHQ-9 Depression Severity Data ────────────────────────────────────────────
# Labels: 0=minimal, 1=mild, 2=moderate, 3=moderately_severe, 4=severe

PHQ9_EXAMPLES = {
    0: [  # Minimal (PHQ-9: 0-4)
        "I'm doing okay today, just a bit tired from work.",
        "Had a good weekend, spent time with friends.",
        "Feeling fine overall, nothing major to report.",
        "A little stressed about deadlines but managing.",
        "Slept well last night, feeling refreshed.",
        "Things are going pretty normally.",
        "Had some ups and downs but mostly positive.",
        "Enjoying my hobbies, feeling motivated.",
        "Good energy levels today.",
        "Life is good, feeling content.",
    ],
    1: [  # Mild (PHQ-9: 5-9)
        "I've been feeling a bit down lately, not sure why.",
        "My energy has been lower than usual this week.",
        "Sometimes I feel like I'm just going through the motions.",
        "Haven't been sleeping great, waking up tired.",
        "Not as interested in things I usually enjoy.",
        "I feel a little hopeless sometimes but it passes.",
        "Some days are harder than others lately.",
        "I've been feeling more irritable than usual.",
        "Hard to concentrate at work recently.",
        "I don't feel as motivated as I used to.",
    ],
    2: [  # Moderate (PHQ-9: 10-14)
        "I've been struggling to get out of bed most mornings.",
        "I feel empty and numb most of the day.",
        "Lost interest in almost everything I used to love.",
        "I feel worthless and like nothing I do matters.",
        "Crying spells have been more frequent lately.",
        "I can't seem to find any joy in daily activities.",
        "My appetite has completely changed, I barely eat.",
        "I feel like a burden to my family.",
        "Concentrating on anything feels impossible.",
        "Most days I feel deeply sad with no clear reason.",
    ],
    3: [  # Moderately severe (PHQ-9: 15-19)
        "I feel completely hopeless, like things will never get better.",
        "I've been sleeping 14 hours a day and still exhausted.",
        "I feel so worthless that I question why I'm even here.",
        "I've stopped responding to messages, I can't face anyone.",
        "Every day feels like an unbearable weight on my chest.",
        "I've had thoughts that I would be better off dead.",
        "I can't remember the last time I felt anything other than pain.",
        "I've been isolating myself completely, pushing everyone away.",
        "Simple tasks feel impossible, I haven't showered in days.",
        "The future feels completely dark and pointless.",
    ],
    4: [  # Severe (PHQ-9: 20-27)
        "I don't see any reason to keep going. The pain is unbearable.",
        "I've been thinking about suicide constantly for weeks.",
        "I feel like dying would be a relief. I'm so tired of fighting.",
        "I have a plan to end my life and I'm not sure I can stop myself.",
        "I've given away my belongings because I don't think I'll need them.",
        "I feel completely detached from life, like I'm already gone.",
        "The darkness never lifts. I've lost all will to live.",
        "I can't stop the thoughts of hurting myself.",
        "I've written goodbye letters to the people I love.",
        "I'm at the end of my rope and I don't know how much longer I can hold on.",
    ],
}

# ── Suicide Risk Data ──────────────────────────────────────────────────────────
# Labels: 0=no_crisis, 1=crisis

CRISIS_EXAMPLES = {
    0: [
        "I've been having a rough time but I'm talking to my therapist.",
        "Feeling sad today but I know it will pass.",
        "Stressed about finances but taking it one day at a time.",
        "My mental health has been challenging but I have support.",
        "Going through a breakup, it's hard but I'm managing.",
        "Having some dark thoughts but I know to call for help.",
        "Feeling overwhelmed but I'm using my coping skills.",
        "Bad anxiety day but I did my breathing exercises.",
        "Grief is hitting hard today but I'm surrounded by people who care.",
        "It's been a tough week mentally but I have a therapy appointment.",
    ],
    1: [
        "I want to kill myself. I have pills ready.",
        "I don't want to be alive anymore. I've made my decision.",
        "I've been cutting myself every night to deal with the pain.",
        "I have a plan to end my life this weekend.",
        "I said goodbye to my family in my head. Tonight is the night.",
        "I can't take this pain anymore. I'm going to end it.",
        "I've been stockpiling medication for an overdose.",
        "I don't want anyone to find me until it's too late.",
        "I'm going to jump. I've found the place.",
        "I've written my note. This is my final message.",
        "No one would miss me. I'm doing everyone a favor by leaving.",
        "I've been hurting myself daily and I want to go further.",
        "I have a gun and I've been thinking about using it.",
        "Every night I wish I won't wake up in the morning.",
        "I'm at a bridge right now. I don't know if I can stop myself.",
    ],
}

# ── Emotion Classification Data ────────────────────────────────────────────────
# Labels: sadness, anxiety, anger, hopelessness, loneliness, shame, numbness, neutral

EMOTION_EXAMPLES = {
    "sadness": [
        "I cry myself to sleep every night missing what we had.",
        "Everything reminds me of the loss and it breaks my heart.",
        "The grief feels like a physical weight I can't carry.",
        "I'm mourning a life I thought I'd have.",
        "Tears come without warning throughout the day.",
        "I feel a deep sadness I can't shake off.",
        "My heart aches constantly and I don't know how to stop it.",
        "I've been crying all day and I don't even know why.",
        "The longing for what I've lost is overwhelming.",
        "I feel heartbroken and devastated.",
        "A profound sadness has settled into my bones.",
        "I miss the person I used to be before all this.",
    ],
    "anxiety": [
        "My heart races every time I think about tomorrow.",
        "I can't stop my mind from spiraling into worst-case scenarios.",
        "Panic attacks are happening multiple times a day now.",
        "I'm terrified of everything and nothing at the same time.",
        "The constant worry is exhausting and I can't switch it off.",
        "I feel a constant sense of dread I can't shake.",
        "My chest tightens whenever I think about going outside.",
        "I lie awake replaying scenarios of things going wrong.",
        "The anxiety is so bad I've been avoiding leaving my house.",
        "I feel on edge all the time like something terrible is coming.",
        "My thoughts race uncontrollably and I can't slow them down.",
        "I'm paralyzed by fear of making the wrong decision.",
    ],
    "anger": [
        "I'm so angry I can feel it in my whole body.",
        "I want to scream at everyone around me.",
        "The rage is overwhelming and I can't control it.",
        "I feel cheated and betrayed and furious.",
        "Everything makes me snap lately, I'm always on edge.",
        "I've been explosive lately over the smallest things.",
        "I feel a burning resentment I can't let go of.",
        "I'm furious at the world and I don't know what to do with it.",
        "My anger comes out of nowhere and I end up hurting people I love.",
        "I feel wronged and the injustice makes me want to explode.",
        "I'm full of rage about my situation and I can't calm down.",
        "The anger consumes me and I say things I later regret.",
    ],
    "hopelessness": [
        "There's no light at the end of this tunnel.",
        "I've given up believing things can change.",
        "The future looks completely empty and dark.",
        "I can't imagine a version of my life that gets better.",
        "Every door I try is locked. There's no way forward.",
        "I've stopped making plans because nothing ever works out.",
        "I feel like I'm trapped with no exit.",
        "The hope I once had is completely gone.",
        "I don't see the point of trying anymore.",
        "Nothing I do makes any difference — it's all meaningless.",
        "I've lost faith that things will ever improve.",
        "The future feels like a blank wall. Nothing is there.",
    ],
    "loneliness": [
        "I'm surrounded by people but feel completely alone.",
        "No one truly understands what I'm going through.",
        "I've never felt so isolated in my entire life.",
        "The silence is deafening. I have no one to call.",
        "I feel invisible, like I could disappear and no one would notice.",
        "I'm disconnected from everyone even when I'm in a crowd.",
        "I have no one to talk to about the real things.",
        "The loneliness is crushing me from the inside.",
        "I reach out but no one reaches back.",
        "I feel like an outsider in my own life.",
        "The isolation has become my normal and it's unbearable.",
        "I'm going through this completely alone.",
    ],
    "shame": [
        "I'm disgusted by myself and what I've become.",
        "I can't look at myself in the mirror.",
        "I'm embarrassed to even exist right now.",
        "I feel like a failure and everyone can see it.",
        "The shame is so deep I can't talk about it with anyone.",
        "I'm humiliated by my own behavior and I can't forgive myself.",
        "I feel worthless and defective as a person.",
        "The shame follows me everywhere and I can't escape it.",
        "I've done things I'm deeply ashamed of and I hate myself for it.",
        "I'm too embarrassed to ask for help.",
        "I feel fundamentally broken and unworthy of love.",
        "The self-loathing is overwhelming.",
    ],
    "numbness": [
        "I don't feel anything anymore. Just empty.",
        "It's like all my emotions have been switched off.",
        "I go through the motions but nothing registers.",
        "I used to feel things but now there's just nothing.",
        "Even the things that should hurt don't affect me.",
        "I'm numb to everything around me.",
        "I watch my life happening but I'm not really there.",
        "The emptiness inside me is complete.",
        "I've become detached from everything I used to care about.",
        "Nothing touches me anymore — I'm just hollow.",
        "I feel like a shell of a person going through routines.",
        "The flatness inside me is terrifying in its own way.",
    ],
    "neutral": [
        "Today was a normal day. Nothing special happened.",
        "I went to work and came home. It was fine.",
        "Things are just continuing as they are.",
        "No major changes, just the usual routine.",
        "It was an ordinary day.",
        "I'm feeling okay, not great not terrible.",
        "Everything is just average right now.",
        "Nothing much to report today.",
        "Just going through the day as normal.",
        "Things are stable, no particular feelings.",
        "Today was pretty unremarkable.",
        "I'm in a neutral place emotionally right now.",
    ],
}


def build_phq9_dataset():
    rows = []
    for label, texts in PHQ9_EXAMPLES.items():
        for text in texts:
            # Augment with slight variations
            rows.append({"text": text, "label": label})
            rows.append({"text": text + " " + random.choice([
                "I don't know what to do.", "It's been going on for weeks.",
                "I'm trying to push through.", "I'm not sure how much longer I can manage.",
                "I hope things improve soon.", ""
            ]), "label": label})
    random.shuffle(rows)
    return rows


def build_crisis_dataset():
    rows = []
    for label, texts in CRISIS_EXAMPLES.items():
        for text in texts:
            rows.append({"text": text, "label": label})
    random.shuffle(rows)
    return rows


def build_emotion_dataset():
    rows = []
    for emotion, texts in EMOTION_EXAMPLES.items():
        for text in texts:
            rows.append({"text": text, "label": emotion})
    random.shuffle(rows)
    return rows


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    phq9 = build_phq9_dataset()
    crisis = build_crisis_dataset()
    emotions = build_emotion_dataset()

    with open("data/phq9_training.json", "w") as f:
        json.dump(phq9, f, indent=2)
    with open("data/crisis_training.json", "w") as f:
        json.dump(crisis, f, indent=2)
    with open("data/emotion_training.json", "w") as f:
        json.dump(emotions, f, indent=2)

    print(f"✅ PHQ-9 dataset:  {len(phq9)} examples")
    print(f"✅ Crisis dataset: {len(crisis)} examples")
    print(f"✅ Emotion dataset:{len(emotions)} examples")
    print("   Saved to data/")
