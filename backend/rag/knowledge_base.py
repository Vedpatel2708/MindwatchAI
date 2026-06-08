"""
backend/rag/knowledge_base.py
Mental health knowledge base — 35+ evidence-based documents
"""

KNOWLEDGE_DOCUMENTS = [

    # ── DEPRESSION ────────────────────────────────────────────────────────────
    {
        "id": "dep-001",
        "title": "Understanding Depression: Core Symptoms",
        "category": "depression",
        "source": "DSM-5 / APA",
        "tags": ["depression", "symptoms", "diagnosis"],
        "content": """Depression (Major Depressive Disorder) is characterized by persistent low mood and loss of interest lasting at least 2 weeks.

Core symptoms (5+ required, including depressed mood OR loss of interest):
- Persistent sadness, emptiness, or hopelessness nearly every day
- Loss of interest or pleasure in almost all activities (anhedonia)
- Significant weight change (>5% body weight in a month) or appetite disturbance
- Sleep disturbance — insomnia or hypersomnia nearly every day
- Psychomotor agitation or slowing observable by others
- Fatigue or loss of energy nearly every day
- Feelings of worthlessness or excessive guilt
- Difficulty thinking, concentrating, or making decisions
- Recurrent thoughts of death or suicidal ideation

Subtypes: Mild (2-3 symptoms), Moderate (4-5), Severe (6+). Must cause significant distress or functional impairment in work, relationships, or daily life.

Prevalence: Affects 280 million people worldwide. Leading cause of disability globally. Women are 2x more likely than men to be diagnosed. Average age of onset: mid-20s but can occur at any age."""
    },
    {
        "id": "dep-002",
        "title": "Behavioral Activation for Depression",
        "category": "depression",
        "source": "Evidence-Based CBT / Martell et al.",
        "tags": ["depression", "treatment", "CBT", "behavioral-activation"],
        "content": """Behavioral Activation (BA) is as effective as antidepressants for mild-to-moderate depression in randomized controlled trials.

Core principle: Depression creates a vicious cycle — low mood leads to withdrawal, withdrawal reduces positive reinforcement, which deepens low mood. BA breaks this cycle through scheduled activity.

Step-by-step approach:
1. Activity monitoring: For one week, track all activities and rate mood (0-10) before and after each
2. Identify patterns: Which activities improve mood? Which worsen it?
3. Values clarification: What matters most to you? (relationships, work, creativity, health, spirituality)
4. Activity scheduling: Schedule 1-2 small values-aligned activities daily
5. Start impossibly small: 5-minute walk > no walk. Lower the bar dramatically when energy is very low
6. Track and adjust: Note mood changes after activities, build on what works

Activities with strongest evidence:
- Aerobic exercise (equivalent to antidepressants — 30 min 3x/week)
- Social interaction (even brief — coffee with one person)
- Creative activities (painting, music, writing)
- Accomplishment tasks (completing one item on to-do list)
- Nature exposure (20 min in green space reduces rumination by 25%)
- Acts of kindness (helping others activates reward circuits)

Key insight: You don't wait to feel motivated before acting. You act, and motivation follows. "Outside-in" rather than "inside-out" change."""
    },
    {
        "id": "dep-003",
        "title": "Cognitive Distortions in Depression",
        "category": "depression",
        "source": "Aaron Beck / Cognitive Therapy",
        "tags": ["depression", "CBT", "cognitive-distortions", "thoughts"],
        "content": """Cognitive distortions are systematic errors in thinking that maintain depression. The depressed brain filters reality to confirm negative beliefs.

The 15 most common distortions:
1. All-or-nothing thinking: "If I'm not perfect, I'm a complete failure"
2. Overgeneralization: "This always happens to me" / "Nothing ever works out"
3. Mental filter: Dwelling on one negative while ignoring positives
4. Disqualifying positives: "That doesn't count — I just got lucky"
5. Mind reading: Assuming others think negatively of you (without evidence)
6. Fortune-telling: "I know it will go wrong"
7. Catastrophizing: Making things much worse than they are
8. Minimization: Making positives trivially small
9. Emotional reasoning: "I feel stupid, therefore I am stupid"
10. Should/must statements: Rigid rules creating guilt and shame
11. Labeling: "I'm a loser" instead of "I made a mistake"
12. Personalization: Taking blame for events outside your control
13. Fallacy of fairness: "Life should be fair" (it isn't, and expecting fairness creates resentment)
14. Fallacy of change: Expecting others to change to make you happy
15. Heaven's reward fallacy: Self-sacrifice expecting a reward that never comes

How to challenge distortions:
- What is the actual evidence for and against this thought?
- What would I tell a close friend who had this thought?
- Am I confusing a thought with a fact?
- What is the most realistic interpretation?
- Even if true, how bad would it really be? Could I cope?"""
    },
    {
        "id": "dep-004",
        "title": "Antidepressant Medications: What You Need to Know",
        "category": "depression",
        "source": "NICE Guidelines / FDA",
        "tags": ["depression", "medication", "antidepressants", "SSRI"],
        "content": """Antidepressant medications are a first-line treatment for moderate-to-severe depression, often used alongside psychotherapy.

Main types:
SSRIs (Selective Serotonin Reuptake Inhibitors) — most commonly prescribed:
- Fluoxetine (Prozac), Sertraline (Zoloft), Escitalopram (Lexapro), Paroxetine (Paxil)
- Work by increasing serotonin availability in synapses
- Side effects: nausea, sexual dysfunction, sleep changes, initial anxiety increase
- Takes 2-6 weeks for full effect

SNRIs (Serotonin-Norepinephrine Reuptake Inhibitors):
- Venlafaxine (Effexor), Duloxetine (Cymbalta)
- Also treats anxiety and chronic pain
- Slightly more activating than SSRIs

Other options:
- Bupropion (Wellbutrin): activating, no sexual side effects, helps with focus
- Mirtazapine: sedating, good for sleep and appetite problems
- TCAs and MAOIs: older, effective but more side effects

Key facts:
- Antidepressants are NOT addictive — but stopping abruptly causes discontinuation syndrome
- Effects stop when medication stops (unlike CBT, which has lasting effects)
- 40-60% of people respond to first antidepressant tried
- If first doesn't work, switching or combining often succeeds
- Always prescribed by a doctor — self-medication is dangerous
- Combining with psychotherapy has better outcomes than either alone"""
    },
    {
        "id": "dep-005",
        "title": "Postpartum Depression: Recognition and Support",
        "category": "depression",
        "source": "Postpartum Support International / APA",
        "tags": ["depression", "postpartum", "pregnancy", "mothers"],
        "content": """Postpartum depression (PPD) affects 1 in 7 new mothers and is distinct from the normal "baby blues" (which resolve within 2 weeks).

Symptoms of PPD:
- Persistent sadness, hopelessness, or emptiness beyond 2 weeks postpartum
- Feeling detached from baby or inability to bond
- Intrusive thoughts about harming baby (very common in PPD — different from intent)
- Severe anxiety or panic attacks
- Inability to sleep even when baby sleeps
- Difficulty making decisions or concentrating
- Feeling like a bad mother or complete failure

Risk factors: History of depression, stressful life events, lack of social support, traumatic birth experience, previous PPD, hormonal sensitivity

Treatment options:
- Therapy (CBT and IPT both effective and safe during breastfeeding)
- SSRIs (Sertraline and Paroxetine have best safety data during breastfeeding)
- Support groups (Postpartum Support International has free helpline: 1-800-944-4773)
- Partner and family support education

Postpartum psychosis (rare, 1-2/1000): sudden onset of hallucinations, delusions, confusion — MEDICAL EMERGENCY, call 911 immediately

Key message: PPD is not a character flaw or weakness. It's a medical condition caused by hormonal changes, sleep deprivation, and the enormous demands of new parenthood. Treatment is effective."""
    },

    # ── ANXIETY ───────────────────────────────────────────────────────────────
    {
        "id": "anx-001",
        "title": "Understanding Anxiety: Types and Symptoms",
        "category": "anxiety",
        "source": "DSM-5 / APA",
        "tags": ["anxiety", "symptoms", "GAD", "panic", "social-anxiety"],
        "content": """Anxiety disorders are the most common mental health conditions worldwide, affecting 284 million people. Anxiety is normal — anxiety disorders are when anxiety becomes excessive and interferes with daily life.

Generalized Anxiety Disorder (GAD):
- Excessive, uncontrollable worry about multiple topics for 6+ months
- Restlessness, fatigue, poor concentration, irritability, muscle tension, sleep problems
- Worry is out of proportion to actual risk
- Very common in perfectionists and high achievers

Panic Disorder:
- Recurrent unexpected panic attacks (intense physical fear response)
- Persistent worry about having more attacks
- Avoidance of situations associated with attacks
- Panic attacks peak within 10 minutes and include: racing heart, shortness of breath, dizziness, chest pain, numbness, fear of dying or losing control

Social Anxiety Disorder:
- Intense fear of social situations due to fear of humiliation or judgment
- Avoidance leads to isolation and missed opportunities
- Distinct from shyness — significantly impacts daily function

Specific Phobias: Fear of specific objects/situations (heights, spiders, flying, needles)

Health Anxiety (Illness Anxiety Disorder): Excessive fear of having a serious illness despite medical reassurance

Physical symptoms of anxiety: Headaches, GI distress, muscle tension, sweating, trembling, rapid heartbeat — all caused by the fight-or-flight response, not "just in your head"."""
    },
    {
        "id": "anx-002",
        "title": "Grounding Techniques for Acute Anxiety and Panic",
        "category": "anxiety",
        "source": "DBT / Trauma-Informed Care / Clinical Research",
        "tags": ["anxiety", "coping", "grounding", "panic", "immediate-relief"],
        "content": """Grounding techniques interrupt anxiety spirals by bringing attention to the present moment. Use these when anxiety is acute or during a panic attack.

5-4-3-2-1 Sensory Grounding (most widely used):
Name out loud or in your head:
5 things you can SEE (details — the grain in wood, a crack in the ceiling)
4 things you can TOUCH (the texture of your clothes, the temperature of air)
3 things you can HEAR (distant sounds, background noise)
2 things you can SMELL
1 thing you can TASTE
Time required: 3-5 minutes. Works by engaging sensory cortex, which competes with fear response.

Physiological Sigh (fastest scientifically validated technique):
Double inhale through nose (sniff-sniff to fully expand lungs), then long slow exhale through mouth.
Mechanism: Reinflates collapsed alveoli and activates parasympathetic system. Used by Stanford neuroscience lab and Navy SEALs.
Time required: 1-2 cycles.

Box Breathing (4-4-4-4):
Inhale 4 counts → Hold 4 → Exhale 4 → Hold 4. Repeat 4 times.
Used by emergency medical personnel and athletes.

Cold Water Dive Response:
Submerge face in cold water or apply cold wet towel to face for 30 seconds.
Activates "mammalian dive reflex" — slows heart rate by 10-25% immediately.

Cognitive Anchor:
Name 5 animals, then 5 countries, then 5 cars.
Engages prefrontal cortex (rational brain) which competes with amygdala (fear brain).

Progressive Muscle Relaxation (for ongoing anxiety):
Systematically tense and release each muscle group from feet to face. 15-20 minutes.
Clinical evidence: reduces anxiety by 20-30% with regular practice."""
    },
    {
        "id": "anx-003",
        "title": "Exposure Therapy: Overcoming Avoidance",
        "category": "anxiety",
        "source": "Evidence-Based CBT / Foa et al.",
        "tags": ["anxiety", "treatment", "exposure-therapy", "avoidance", "CBT"],
        "content": """Exposure therapy is the gold-standard treatment for all anxiety disorders. Over 600 studies demonstrate its effectiveness. 70-90% of people with specific phobias recover with 1-5 sessions.

Why avoidance is the engine of anxiety:
Every time you avoid a feared situation, you get immediate relief (negative reinforcement), which teaches your brain that avoidance = safety. The fear grows with each avoidance. The situation itself never gets a chance to feel safe.

Building a fear hierarchy:
1. List every situation, object, or activity you avoid due to anxiety
2. Rate each 0-100 (Subjective Units of Distress, SUDS)
3. Order from least to most feared
4. Begin at 30-50 SUDS (challenging but manageable)

During exposure:
- Stay in the feared situation until anxiety naturally decreases (habituation)
- Do NOT leave until anxiety has reduced by at least 50%
- Expect anxiety to peak then fall — this is normal
- The goal is learning, not comfort
- Inhibitory learning: building a new "it's safe" memory alongside the old fear memory

Types of exposure:
- In vivo: Real-life contact with feared situation (most effective)
- Imaginal: Vivid mental imagery of feared scenario (useful for OCD, PTSD, social anxiety)
- Interoceptive: Deliberately inducing feared body sensations (spinning chair for dizziness, exercise for racing heart) — used in panic disorder
- Virtual Reality: Computer-generated environments — growing evidence base

What NOT to do during exposure:
- Safety behaviors (holding rail, having phone ready to call someone, checking for exits)
- Distraction (listening to music, scrolling phone)
Both reduce learning — anxiety must be fully experienced for habituation to occur"""
    },
    {
        "id": "anx-004",
        "title": "Managing Anxiety Without Medication",
        "category": "anxiety",
        "source": "Multiple RCTs / NICE Guidelines",
        "tags": ["anxiety", "treatment", "non-medication", "lifestyle", "self-help"],
        "content": """Many people effectively manage anxiety without medication using evidence-based strategies. These approaches work for mild-to-moderate anxiety and can complement medication for severe anxiety.

Evidence-based non-medication approaches:

1. CBT (Cognitive Behavioral Therapy):
Most effective psychological treatment for anxiety. Teaches thought challenging + gradual exposure. 12-16 sessions typical. Available via therapist, online platforms (Anxiety Coach), or self-help books (recommended: "Anxiety and Worry Workbook" by Clark & Beck).

2. Exercise:
150 min moderate aerobic activity per week reduces anxiety by 48% in clinical studies. Mechanism: reduces cortisol, increases GABA (calming neurotransmitter), burns off adrenaline. Effect visible after 2-4 weeks of regular practice.

3. Mindfulness Meditation:
Mindfulness-Based Stress Reduction (MBSR) — 8-week program — reduces anxiety by 38% in multiple meta-analyses. Apps: Headspace, Calm, Insight Timer. Start with 10 minutes daily.

4. Reducing Stimulants:
Caffeine directly worsens anxiety by mimicking the physical anxiety response (racing heart, jitteriness). Try eliminating or reducing coffee/energy drinks for 2 weeks and note the difference.

5. Sleep Optimization:
Anxiety worsens dramatically with poor sleep. Sleep deprivation increases anxiety by 30% (UC Berkeley study). Prioritize 7-9 hours with consistent wake time.

6. Breathing Regulation:
Anxiety causes fast shallow breathing, which causes physical anxiety symptoms (dizziness, tingling). Slow diaphragmatic breathing (4 counts in, 6 counts out) directly counteracts this.

7. Social Support:
Talking about anxiety with trusted people reduces its intensity. Support groups and online communities also helpful (AnxietyUK, ADAA online support)."""
    },

    # ── CRISIS INTERVENTION ────────────────────────────────────────────────────
    {
        "id": "cri-001",
        "title": "Suicide Warning Signs and Risk Assessment",
        "category": "crisis",
        "source": "AFSP / Columbia Suicide Severity Rating Scale",
        "tags": ["crisis", "suicide", "warning-signs", "safety", "risk-assessment"],
        "content": """Suicide is preventable. Recognizing warning signs and acting quickly saves lives.

DIRECT warning signs (require immediate action):
- Talking about wanting to die or kill oneself
- Searching online for methods of suicide
- Talking about being a burden to others
- Saying "Everyone would be better off without me"
- Giving away prized possessions
- Saying goodbye as if for the last time
- Acquiring means (buying a gun, stockpiling medications)

BEHAVIORAL warning signs:
- Dramatic changes in mood (sudden calmness after depression can indicate a decision)
- Increased substance use
- Withdrawing from friends, family, and activities
- Extreme recklessness (driving fast, unsafe sex, drug use)
- Sleeping too much or too little
- Displaying intense rage or talking about revenge

ASK directly: "Are you thinking about suicide?"
Research shows asking does NOT plant the idea — it opens the door for help and shows you care.

RISK LEVELS:
- Ideation without plan: Moderate risk — needs support and monitoring
- Ideation with plan: High risk — needs immediate professional help
- Ideation with plan + means + timeline: IMMINENT danger — call 911

PROTECTIVE FACTORS (reduce risk):
- Reasons for living (children, pets, faith, unfinished goals)
- Strong social connections
- Engagement with mental health treatment
- Problem-solving ability
- Cultural or religious beliefs that discourage suicide
- Access to mental health care

CRISIS RESOURCES:
- 988 Suicide & Crisis Lifeline: call or text 988 (US)
- Crisis Text Line: text HOME to 741741
- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/
- Emergency: 911"""
    },
    {
        "id": "cri-002",
        "title": "How to Help Someone in Suicidal Crisis",
        "category": "crisis",
        "source": "NAMI / QPR Institute / Mental Health First Aid",
        "tags": ["crisis", "helping-others", "suicide", "first-aid"],
        "content": """QPR (Question, Persuade, Refer) is the most widely trained crisis intervention approach.

QUESTION — Ask directly:
"I've noticed you seem really down lately. Are you thinking about suicide?"
"Are you having thoughts of hurting yourself?"
Be direct. Beating around the bush sends the message the topic is too taboo to discuss.

PERSUADE — Listen and connect:
Do: Listen without judgment. Say "Thank you for telling me." Validate their pain ("That sounds unbearable"). Stay calm.
Don't: Argue. Promise confidentiality. Leave them alone. Say "But you have so much to live for" (dismisses their reality).

Validation statements:
"I hear how much pain you're in."
"It makes sense you feel this way given everything you've been through."
"I'm glad you're talking to me. You don't have to face this alone."

REFER — Connect to help:
"Will you call 988 with me right now?"
"Can I take you to the emergency room?"
"Let me help you call your therapist."
"Will you promise not to hurt yourself tonight while we find you help?"

Means restriction (reduces risk 30-90%):
Gently ask about access to lethal means (especially firearms and medications).
Ask family to temporarily store or secure weapons and medications.
"Could we put those pills somewhere less accessible for now?"

After immediate crisis:
Follow up — text or call the next day. People in crisis often feel shame after disclosing.
Your ongoing connection matters as much as the initial intervention."""
    },
    {
        "id": "cri-003",
        "title": "Safety Planning: A Personalized Crisis Plan",
        "category": "crisis",
        "source": "Stanley-Brown Safety Planning Intervention",
        "tags": ["crisis", "safety-plan", "suicide-prevention", "coping"],
        "content": """A safety plan is a written, personalized crisis plan created in calm times to use during a crisis. More effective than "no-harm contracts." Standard of care for suicidal ideation.

The 6 steps of a safety plan (complete in advance with a clinician):

Step 1 — Warning signs:
Personal triggers, thoughts, images, moods, situations that signal a crisis is approaching.
Example: "I start thinking 'no one cares about me' and stop responding to messages."

Step 2 — Internal coping strategies:
Things to do ALONE to distract or self-soothe (without calling others).
Example: "Go for a run. Listen to my playlist. Draw in my sketchbook."

Step 3 — Social contacts for distraction:
People and social settings that provide distraction from crisis (not necessarily aware of crisis).
Example: "Call my sister and ask about her kids." "Go to coffee shop."

Step 4 — People I can tell I'm struggling:
Trusted individuals who know about the crisis and can offer support.
Name + phone number of 2-3 people.

Step 5 — Professional resources:
Therapist name and number. Crisis line (988). Nearest emergency room address.

Step 6 — Making environment safe:
Removing or restricting access to lethal means.
Example: "Give sleep medications to my partner to hold."

Implementation:
Keep the plan accessible — on phone, on refrigerator.
Review with clinician at every appointment.
Practice using earlier steps before crisis becomes severe."""
    },

    # ── COPING STRATEGIES ──────────────────────────────────────────────────────
    {
        "id": "cop-001",
        "title": "Mindfulness-Based Approaches for Mental Health",
        "category": "coping",
        "source": "MBSR / Kabat-Zinn / 600+ RCTs",
        "tags": ["coping", "mindfulness", "meditation", "depression", "anxiety"],
        "content": """Mindfulness — paying attention to the present moment without judgment — has the largest evidence base of any psychological intervention: 600+ randomized controlled trials.

What mindfulness changes in the brain (neuroimaging studies):
- Reduces amygdala reactivity (less automatic fear response)
- Increases prefrontal cortex thickness (better emotion regulation)
- Strengthens the anterior cingulate cortex (attention control)
- Reduces default mode network activity (rumination and mind-wandering)

Evidence for specific conditions:
- Depression relapse prevention: MBCT (Mindfulness-Based Cognitive Therapy) reduces relapse by 43% in people with 3+ depressive episodes — equivalent to antidepressants for prevention
- Anxiety: MBSR reduces anxiety by 38% (meta-analysis of 39 studies)
- Chronic pain: Reduces pain intensity and improves quality of life
- PTSD: Reduces hyperarousal and intrusion symptoms

Core practices for beginners:

Breath Awareness (5 minutes):
Sit comfortably. Gently focus on the physical sensation of breathing.
When mind wanders (it will), simply notice "thinking" and return to breath.
This IS the practice — the noticing and returning, not the absence of thoughts.

Body Scan (15-20 minutes):
Systematically move attention through body from feet to head.
Notice sensations without trying to change them.
Particularly effective for anxiety and dissociation.

Mindful Walking:
Walk slowly, noticing each step, the sensation of foot meeting ground.
Eyes open, awareness of surroundings.
Accessible for people who struggle with seated meditation.

Resources: Headspace, Calm, Ten Percent Happier (apps); MBSR.com for 8-week programs; Jon Kabat-Zinn books"""
    },
    {
        "id": "cop-002",
        "title": "DBT Skills: Distress Tolerance and Emotion Regulation",
        "category": "coping",
        "source": "Marsha Linehan / DBT Skills Training Manual",
        "tags": ["coping", "DBT", "emotion-regulation", "distress-tolerance"],
        "content": """DBT (Dialectical Behavior Therapy) provides concrete skills for managing intense emotions and crises.

DISTRESS TOLERANCE — For surviving crises without making things worse:

TIPP Skills (change body chemistry fast):
- Temperature: Cold water on face (activates dive reflex, slows heart rate immediately)
- Intense exercise: 20 minutes vigorous activity burns off adrenaline
- Paced breathing: Slow down breathing to 4-6 breaths per minute
- Progressive relaxation: Tense and release muscle groups

ACCEPTS (distract from crisis temporarily):
- Activities: Engage in an absorbing activity
- Contributing: Do something for someone else
- Comparisons: Compare to past hard times you survived
- Emotions (opposite): Watch a funny movie when sad
- Pushing away: Mentally put the problem in a box temporarily
- Thoughts: Count to 100, recite song lyrics
- Sensations: Hold ice cube, listen to loud music

Self-Soothe with five senses:
Vision: Look at beautiful art or nature
Hearing: Calming or energizing music
Smell: Scented candle, essential oils
Taste: Mindfully eat your favorite food
Touch: Soft blanket, warm bath

EMOTION REGULATION — For changing how you feel:

PLEASE skills (reduce vulnerability to intense emotions):
PhysicaL illness: Treat infections, injuries
Eating: Regular balanced meals, no alcohol
Avoid mood-altering substances
Sleep: 7-9 hours with consistent schedule
Exercise: 150 min/week aerobic activity

Opposite Action:
Identify emotion's action urge → Do the OPPOSITE
Fear says: avoid → Approach gradually
Shame says: hide → Share appropriately
Sadness says: isolate → Reach out
Anger says: attack → Be gentle"""
    },
    {
        "id": "cop-003",
        "title": "Exercise as Mental Health Treatment",
        "category": "coping",
        "source": "150+ RCTs / NICE Guidelines / Harvard Medical School",
        "tags": ["coping", "exercise", "depression", "anxiety", "evidence-based"],
        "content": """Exercise is one of the most evidence-based mental health interventions available, with effects comparable to antidepressants for mild-to-moderate depression.

Key research findings:
- Meta-analysis of 49 studies: Exercise reduces depression by 0.67 standard deviations (equivalent to antidepressant effect)
- 30 min aerobic exercise 3x/week as effective as Zoloft (Blumenthal et al., Duke University)
- Exercise reduces anxiety by 48% in clinical populations
- Effects appear in 2-4 weeks of consistent exercise
- Effects lost when exercise stops (maintenance required)
- Combined exercise + therapy > either alone

Mechanisms (why exercise works for mental health):
- Increases BDNF (Brain-Derived Neurotrophic Factor) — promotes neuroplasticity and neurogenesis
- Increases serotonin, dopamine, and norepinephrine (same neurotransmitters targeted by antidepressants)
- Reduces cortisol (stress hormone) and inflammation (elevated in depression)
- Improves sleep quality (bidirectional benefit)
- Behavioral activation: provides structure, accomplishment, and social contact
- Reduces amygdala reactivity (less reactive to threats)

Dosage (minimum effective dose):
- 150 minutes moderate aerobic activity per week (NICE guidelines)
- 3x30 minutes shows clinical benefit
- Even 10-20 minutes shows measurable mood improvement
- Aerobic exercise has strongest evidence (running, swimming, cycling, brisk walking)
- Resistance training also effective, especially for anxiety

Starting when depressed (key strategy — start impossibly small):
Week 1: 5-minute walk daily (do this without negotiation)
Week 2: 10-minute walk
Week 3: 15-20 minutes, 3x/week
After 4 weeks: energy and motivation begin to improve, enabling more activity

For anxiety: High-intensity aerobic exercise is particularly effective — mimics and exhausts the physical anxiety response, teaching the body that arousal is survivable"""
    },
    {
        "id": "cop-004",
        "title": "Sleep Hygiene and CBT for Insomnia",
        "category": "coping",
        "source": "CBT-I / American Academy of Sleep Medicine",
        "tags": ["coping", "sleep", "insomnia", "CBT-I", "depression", "anxiety"],
        "content": """Sleep and mental health are bidirectionally related: poor sleep worsens mental health, and mental health problems worsen sleep. CBT-I (CBT for Insomnia) is more effective than sleep medication.

Impact of poor sleep on mental health:
- Sleep deprivation increases anxiety reactivity by 30% (UC Berkeley)
- Chronic insomnia increases depression risk 4x
- After one night of poor sleep: reduced empathy, increased irritability, decreased cognitive function
- Sleep is when the brain consolidates emotional memories and processes trauma

CBT-I components (more effective than Ambien, no side effects):

1. Sleep Restriction Therapy:
Calculate your actual sleep time (not time in bed). Restrict time in bed to match actual sleep + 30 min.
Example: If sleeping 5 hours but in bed 9 hours, only allow 5.5 hours in bed.
This builds "sleep pressure" and consolidates sleep.
Gradually extend by 15-30 min when sleep efficiency >85%.

2. Stimulus Control (most important single technique):
Bed = sleep + sex ONLY. No phone, no TV, no lying awake worrying.
If awake >20 minutes, get up and do something calm until sleepy.
Wake at the same time every day (yes, weekends too).

3. Sleep Hygiene:
- Consistent wake time (most important — sets circadian rhythm)
- No screens 60 minutes before bed (blue light suppresses melatonin)
- Keep bedroom cool (65-68°F / 18-20°C ideal)
- No caffeine after 2pm
- No alcohol (disrupts sleep architecture, reduces REM sleep)
- No naps over 20 minutes or after 3pm

4. Cognitive Restructuring:
Common dysfunctional beliefs: "I MUST get 8 hours or I'll fail tomorrow"
Reality: Performance declines but remains functional with 6 hours. One bad night won't ruin you.

5. Relaxation Techniques:
Progressive muscle relaxation or 4-7-8 breathing before bed"""
    },
    {
        "id": "cop-005",
        "title": "Journaling and Expressive Writing for Mental Health",
        "category": "coping",
        "source": "James Pennebaker / 200+ Studies",
        "tags": ["coping", "journaling", "expressive-writing", "processing", "self-help"],
        "content": """Expressive writing (journaling about thoughts and feelings) has 200+ studies showing significant mental health benefits.

Pennebaker Protocol (most studied approach):
Write continuously for 20 minutes on 4 consecutive days.
Write about your deepest thoughts and feelings about a difficult experience.
Include both facts AND emotional reactions.
The writing is private — no performance or grammar required.

Evidence-based outcomes (vs. non-emotional writing control groups):
- Fewer doctor visits in following 3 months
- Stronger immune function (T-lymphocyte levels)
- Reduced PTSD symptoms
- Lower depression scores
- Higher academic GPA in college students

Why it works:
- Translates emotional experience into language (narrative processing)
- Creates coherent story from chaotic experience
- Reduces intrusive thoughts by "completing" the emotional processing
- Increases insight and perspective-taking
- Reduces rumination (thoughts externalized onto paper rather than cycling in mind)

Specific journaling approaches:

Gratitude Journaling (for depression):
Write 3 specific things you're grateful for each morning.
Be SPECIFIC ("Sarah texted me today" not "my friends").
Specificity matters — general gratitude loses its effect.
After 8 weeks: measurable reduction in depression and increase in wellbeing.

Worry Journaling (for anxiety):
Designated worry time: 20 minutes daily at same time.
Write ALL worries. Analyze which are solvable (make a plan) vs. unsolvable (accept).
When worries arise outside this time: "I'll address this at worry time."

Mood Tracking:
Track daily: mood (1-10), sleep hours, exercise, social contact, notable events.
After 2-4 weeks: reveals patterns and triggers invisible in the moment."""
    },

    # ── THERAPY TYPES ───────────────────────────────────────────────────────────
    {
        "id": "the-001",
        "title": "Cognitive Behavioral Therapy (CBT): How It Works",
        "category": "therapy",
        "source": "Aaron Beck / NICE Guidelines / APA",
        "tags": ["therapy", "CBT", "evidence-based", "depression", "anxiety"],
        "content": """CBT is the most researched psychological treatment. Recommended as first-line treatment for depression and anxiety by NICE (UK), APA, and WHO.

The CBT model:
Situations → Automatic Thoughts → Emotions → Behaviors (all interconnected)
CBT doesn't change situations. It changes how you think about them, which changes how you feel and act.

Core CBT techniques:

Thought Records:
1. Identify: What was the automatic thought? ("I'm going to fail this presentation")
2. Emotion: What emotion? How intense (0-100%)? (Anxiety — 80%)
3. Evidence: What evidence supports the thought? What contradicts it?
4. Balanced thought: "I'm nervous but I've prepared and know this material"
5. Re-rate: Anxiety — 45%

Behavioral Experiments:
Test predictions in real life. "I predicted they'd ignore me. Let's test it."
Collect actual evidence to update beliefs, rather than assuming.

Problem-Solving Training:
1. Define the problem specifically
2. Brainstorm all possible solutions (no evaluation — quantity over quality)
3. Evaluate pros and cons of each
4. Choose best option and implement
5. Review results and adjust

Activity Scheduling and Graded Task Assignment:
Breaking overwhelming tasks into small manageable steps.
Scheduling pleasant and accomplishment activities to improve mood.

Structure of CBT:
- 12-20 sessions, typically weekly
- Highly structured: agenda, homework, skills practice
- Therapist is collaborative coach, not expert
- Homework is essential — practice between sessions drives change

Effectiveness:
- Depression: 60-80% response rate
- Anxiety disorders: 70-90% response rate
- Effects last after therapy ends (unlike medication which stops working when stopped)
- Available as self-help (books, apps), online therapy, or face-to-face"""
    },
    {
        "id": "the-002",
        "title": "When and How to Seek Mental Health Help",
        "category": "therapy",
        "source": "APA / SAMHSA / WHO",
        "tags": ["therapy", "seeking-help", "barriers", "finding-therapist"],
        "content": """The average gap between first symptoms and first treatment is 11 years. Early intervention dramatically improves outcomes.

When to seek help:
- Symptoms lasting more than 2 weeks
- Symptoms significantly interfere with work, relationships, or daily activities
- Using alcohol or drugs to cope
- Thoughts of harming yourself or others
- Self-help strategies haven't helped
- People close to you are expressing concern

Types of mental health professionals:
Psychiatrist: Medical doctor (MD/DO), can prescribe medication, provides diagnosis, sometimes therapy
Psychologist: PhD/PsyD, specializes in assessment and psychotherapy, cannot prescribe (in most states)
Licensed Therapist (LCSW, LPC, MFT): Master's level, provides therapy, cannot prescribe
Primary Care Physician: First point of contact, can screen, prescribe antidepressants, and refer

How to find affordable therapy:
- Open Path Collective: openpathhealthcare.org — $30-80/session for lower income
- Psychology Today directory: psychologytoday.com/us/therapists (filter by insurance, fee)
- SAMHSA treatment locator: findtreatment.gov or 1-800-662-4357 (free, confidential)
- Community Mental Health Centers: Sliding scale, income-based fees
- University training clinics: Low-cost therapy by supervised graduate students
- Employee Assistance Programs (EAP): Check with employer — often 3-6 free sessions
- Online therapy: BetterHelp, Talkspace (lower cost, accessible)

First session expectations:
- Therapist gathers history, asks about symptoms and goals
- Collaborative — you can and should share your preferences
- Good fit matters — it's okay to try a few therapists

Overcoming barriers:
Cost: Sliding scale, community centers, online options
Time: Many therapists offer evenings/weekends; online therapy is flexible
Stigma: Mental health conditions are medical conditions, not weakness
"I don't know what to say": Just describe what's been hard lately"""
    },
    {
        "id": "the-003",
        "title": "EMDR Therapy for Trauma and PTSD",
        "category": "therapy",
        "source": "EMDR International Association / WHO Guidelines",
        "tags": ["therapy", "trauma", "PTSD", "EMDR", "evidence-based"],
        "content": """EMDR (Eye Movement Desensitization and Reprocessing) is a WHO-recommended treatment for PTSD and trauma. Considered as effective as trauma-focused CBT.

How EMDR works:
During EMDR, the therapist guides the client to recall traumatic memories while simultaneously performing bilateral stimulation (eye movements, taps, or tones alternating left/right).

Proposed mechanism (Adaptive Information Processing model):
Traumatic memories are "stuck" in the nervous system in raw, unprocessed form — stored with the original emotions, sensations, and distorted beliefs intact.
Bilateral stimulation may mimic the natural processing that occurs during REM sleep, allowing the brain to reprocess and integrate the memory into adaptive memory networks.
After successful EMDR, the memory remains but loses its emotional charge.

Structure of EMDR:
Phase 1-2: History taking, preparation, establishing coping resources
Phase 3: Identifying the target memory, negative belief, emotion, and body sensation
Phase 4: Desensitization — bilateral stimulation while attending to the memory
Phase 5: Installation — strengthening a positive belief
Phase 6: Body scan — checking for residual body tension
Phase 7-8: Closure and re-evaluation

Evidence:
- Multiple RCTs show PTSD remission in 60-80% of single-trauma survivors after 8-12 sessions
- Faster than traditional talk therapy for trauma
- WHO, APA, VA, and DoD all recommend EMDR for PTSD
- Also used for: phobias, grief, chronic pain, performance anxiety

Who is EMDR for? Anyone with traumatic memories that cause current distress: accidents, assault, abuse, medical trauma, combat, disaster"""
    },

    # ── SELF-CARE AND WELLNESS ─────────────────────────────────────────────────
    {
        "id": "sel-001",
        "title": "Nutrition and the Gut-Brain Axis",
        "category": "self-care",
        "source": "Nutritional Psychiatry / Felice Jacka / Gut-Brain Research",
        "tags": ["self-care", "nutrition", "diet", "gut-brain", "depression"],
        "content": """Nutritional psychiatry is the evidence-based field studying how diet affects mental health. The Mediterranean diet reduces depression risk by 33%.

The gut-brain connection:
- 95% of serotonin is produced in the gut, not the brain
- 100 million neurons line the gastrointestinal tract (enteric nervous system)
- The gut microbiome communicates with the brain via the vagus nerve, immune system, and metabolites
- Gut dysbiosis (imbalanced microbiome) is consistently associated with depression and anxiety
- Probiotics in clinical trials show significant reductions in depression and anxiety scores

Foods that support mental health:
Omega-3 fatty acids: Salmon, sardines, mackerel, walnuts, flaxseed
- Anti-inflammatory effects, support neuroplasticity and BDNF production
- Low omega-3 levels consistently associated with depression

Fermented foods (support gut microbiome): Yogurt, kefir, kimchi, sauerkraut, miso, kombucha

Dark leafy greens (folate/B9): Spinach, kale, Swiss chard
- Folate deficiency strongly associated with depression
- Required for serotonin synthesis

Whole grains: Oats, brown rice, quinoa
- Stabilize blood sugar, preventing mood-disrupting spikes and crashes

Berries: Blueberries, strawberries (highest antioxidant content)
- Reduce neuroinflammation, support brain health

Legumes: Beans, lentils (high in fiber, feeding beneficial gut bacteria)

Dark chocolate (70%+): Flavonoids support BDNF and reduce cortisol

Foods to limit:
- Ultra-processed foods: Associated with 58% increased depression risk (meta-analysis)
- Refined sugar: Causes blood sugar spikes → crashes → irritability, fatigue, low mood
- Alcohol: Central nervous system depressant, disrupts sleep, depletes B vitamins, worsens anxiety
- Trans fats: Associated with 48% increased depression risk"""
    },
    {
        "id": "sel-002",
        "title": "Building Social Support for Mental Health",
        "category": "self-care",
        "source": "Holt-Lunstad Meta-analysis / Social Neuroscience",
        "tags": ["self-care", "social-connection", "loneliness", "relationships"],
        "content": """Social connection is one of the strongest predictors of mental and physical health. Loneliness is as harmful as smoking 15 cigarettes per day (Holt-Lunstad meta-analysis of 148 studies, 300,000 participants).

Evidence on social connection:
- Strong social relationships increase survival odds by 50%
- Loneliness increases depression risk by 26% and anxiety by similar amount
- Social support buffers against effects of stress, reducing cortisol response
- Even "weak ties" (regular interactions with acquaintances) significantly predict wellbeing
- Online social connections can supplement but not fully replace in-person contact

Why depression and anxiety cause isolation:
Low energy makes social interaction feel overwhelming → Avoidance → Reduced positive social reinforcement → Deepened isolation → Worsened depression. Classic vicious cycle.

Breaking the isolation cycle (gradual approach):

When severely isolated (start here):
- Text one person today (don't wait to feel like it)
- Say hello to one person outside your home daily (barista, neighbor, cashier counts)
- Reply to one message you've been avoiding

Building connections (when stable enough for this):
- Reconnect with one old friend per month
- Join an interest-based group (book club, hiking group, art class, online community)
- Volunteer regularly (structured social contact + sense of purpose + contribution)
- Be a "regular" at one place (coffee shop, yoga class, gym)
- Consider a pet (consistent social/emotional bond)

Quality over quantity:
Having 1-2 close confidants predicts wellbeing better than having many acquaintances.
Depth of connection matters more than frequency.

For social anxiety specifically:
Use exposure hierarchy — start with brief, low-stakes interactions and gradually increase duration and intimacy."""
    },
    {
        "id": "sel-003",
        "title": "Stress Management: Evidence-Based Strategies",
        "category": "self-care",
        "source": "APA / Mind / Clinical Psychology Research",
        "tags": ["self-care", "stress", "stress-management", "coping", "burnout"],
        "content": """Chronic stress is a major risk factor for depression, anxiety, cardiovascular disease, and immune dysfunction. The stress response (cortisol, adrenaline) is healthy short-term but harmful when chronic.

Understanding your stress response:
- Acute stress: Fight-or-flight response — adaptive, time-limited
- Chronic stress: Cortisol remains elevated → inflammation, hippocampal damage, immune suppression
- Burnout: Emotional exhaustion + depersonalization + reduced efficacy from chronic workplace stress

Evidence-based stress reduction strategies:

1. Problem-Focused Coping (for controllable stressors):
Take direct action to reduce the stressor. Break into manageable steps. Time management. Setting limits on workload.

2. Emotion-Focused Coping (for uncontrollable stressors):
Reframing perspective. Acceptance. Finding meaning. Seeking social support.

3. Social Support:
Talking to trusted others reduces cortisol (literally — social contact is physiologically calming).

4. Physical Activity:
30 minutes moderate exercise burns off stress hormones. Consistent evidence across 100+ studies.

5. Time in Nature:
"Green exercise" (activity in natural environments) reduces cortisol more than indoor exercise.
Even 20 minutes in a park reduces stress hormones significantly.

6. Cognitive Reappraisal:
Changing interpretation of the stressor: "This is a challenge I can learn from" vs "This is a catastrophe."
Stanford research: viewing stress as energizing (vs. harmful) improves performance and health.

7. Relaxation Response (Herbert Benson):
20 minutes daily of relaxation practice (meditation, progressive relaxation, yoga, prayer) literally counters the stress response at the physiological level.

Warning signs of burnout:
Chronic exhaustion not relieved by rest, cynicism and detachment, reduced performance, physical symptoms (headaches, GI problems, frequent illness). Seek professional help if experiencing these symptoms."""
    },
]
