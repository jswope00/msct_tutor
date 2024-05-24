########  GENERAL APP INFORMATION  ##############

APP_TITLE = "Modified Script Concordance Test (mSCT) Tutor"
APP_INTRO = """This is an AI tutor that presents interactive medical case studies with diagnosis and treatment scenarios. 

"""

APP_HOW_IT_WORKS = """
            This is an **AI-Tutored Rubric exercise** that acts as a tutor guiding a student through a shared asset, like an article. It uses the OpenAI Assistants API with GPT-4. The **questions and rubric** are defined by a **faculty**. The **feedback and the score** are generarated by the **AI**. 

It can:

1. provide feedback on a student's answers to questions about an asset
2. roughly "score" a student to determine if they can move on to the next section.  

Scoring is based on a faculty-defined rubric on the backend. These rubrics can be simple (i.e. "full points if the student gives a thoughtful answer") or specific with different criteria and point thresholds. The faculty also defines a minimum pass threshold for each question. The threshold could be as low as zero points to pass any answer, or it could be higher. 

Using AI to provide feedback and score like this is a very experimental process. Some things to note: 

 - AIs make mistakes. Users are encourage to skip a question if the AI is not understanding them or giving good feedback. 
 - The AI might say things that it can't do, like "Ask me anything about the article". I presume further refinement can reduce these kinds of responses. 
 - Scoring is highly experimental. At this point, it should mainly be used to gauge if a user gave an approximately close answer to what the rubric suggests. It is not recommended to show the user the numeric score. 

 """

SHARED_ASSET = {
}

HTML_BUTTON = {}

COMPLETION_MESSAGE = "You've reached the end! I hope you feel a little more prepared for the mSCT exam. Feel free to refresh the page and try another disease!"
COMPLETION_CELEBRATION = False

SCORING_DEBUG_MODE = True

 ####### PHASES INFORMATION #########

PHASES = {
    "disease": {
        "type": "selectbox",
        "label": """Enter a disease to practice your illness scripts.""",
        "options": ["60-year-old woman with chronic cough", "elderly man has dementia"],
        "skip_run": True,
        "ai_response": """Let's practice on the following case: 

Your next appointment is with a 60-year-old woman who is being evaluated for a chronic cough. She has a history of cough for 8 months, and during the examination, you auscultate a left apical systolic murmur.\n

If you were initially thinking of the following diagnosis: Pulmonary edema (left-sided congestive heart failure)

And then you determine the following from the patient's physical exam: Her heart rate is 70 beats/min, and thoracic auscultation reveals crackles bilaterally.

Would the new information make my decision:
+1 More likely, 
0 Neither more nor less likely,
-1 Less likely ?'""",
        "instructions": """
        This is the case the user has been presented with:
        ========

        Case: Your next appointment is with a 60-year-old woman who is being evaluated for a chronic cough. She has a history of cough for 8 months, and during the examination, you auscultate a left apical systolic murmur.

        If you were initially thinking of the following diagnosis: Pulmonary edema (left-sided congestive heart failure)

        And then you determine the following from the patient's physical exam: Her heart rate is 70 beats/min, and thoracic auscultation reveals crackles bilaterally.

        Would the new information make my decision 
        +1 More likely, 
        0 Neither more nor less likely,
        -1 Less likely ?'
        ==========
        Next, they will provide a rating and a rationale for their rating. 
        """
    },
    "likert": {
        "type": "selectbox",
        "options": ['+1 More likely', '0 Neither more nor less likely', '-1 Less likely'],
        "label": """Would the new information make your decision:""",
        "button_label": "Submit",
        "scored_phase": False,
        "instructions": """ The user reacts to the second statement you provided with a likert scale rating indicating if they are more or less likely to stick with the original diagnosis. Please respond verbatim "Thank you for your response. Please provide a justification in the next step".
        """,
        "user_input": "",
        "allow_skip": True
    },
    "rationale": {
       "type": "text_area",
       "height": 200,
       "value": "The presence of bilateral crackles reinforces the likelihood of pulmonary edema caused by left-sided heart failure. Therefore, the new information makes the diagnosis of pulmonary edema more likely.",
       "label": "Please provide written justification for your chosen Likert ranking.",
       "instructions": """
The user will provide a written rationale for their ranking. 
They should explain their thought process, how they used the key features or information to make their decision and provide a defense for their answer using background knowledge. 

You will then generate a percentage estimated probability for the diagnosis, diagnostic testing, or treatment based on the information given. 
For example: 'Estimated probability: 75%. Please note that this percentage is an educational guess and should not replace clinical judgment or professional diagnostic procedures.'
Next, you generate a justification expected from typical expert responses. 
For example: 'The presence of recurrent yeast infections in the patients history is more indicative of diabetes rather than hypothyroidism. Diabetes can lead to elevated blood sugar levels, creating a favorable environment for yeast overgrowth. In contrast, yeast infections are not typically associated with hypothyroidism. Therefore, the new information increases the likelihood of the initial diagnosis of diabetes.'
Then, you compare the expert justification to that entered by the user, offering feedback comparing their choices to typical expert responses, and suggesting areas for improvement or affirmation. 
Then, highlight what the user got wrong compared to the expert justification. 
For example: '**What you got wrong:**\n [What they got wrong compared to the expert]'
Then, highlight what the user got right compared to the expert justification. 
For example: '**What you got right:**\n [What they got right compared to the expert]'
        """,   
       "allow_skip": True
    }
    # "reflect": {
    #    "type": "text_area",
    #    "height": 100,
    #    "label": "Now, please reflect on this exercise",
    #    "button_label": "Finish",
    #    "value":"I think I did well on this exercise and I'm glad that I got immediate feedback. ",
    #    "instructions": """The user is reflecting on their experience. Acknowlege their reflection. 
    #     """,   
    #    "scored_phase": True,
    #    "rubric": """
    #            1. Correctness
    #                1 point - The user has added an appropriate reflection
    #                0 points - The user has not added an appropriate reflection
    #            """,
    #    "minimum_score": 1,
    #    "user_input": "",
    #    "ai_response": "",
    #    "allow_skip": True

    # #Add more steps as needed
    # }
}

########## AI ASSISTANT CONFIGURATION #######
ASSISTANT_NAME = "MsCT Tutor"
ASSISTANT_INSTRUCTIONS = """
Your role is to assist in medical education by presenting and guiding a student through an interactive case study. You will generate a scenario where users can practice diagnosing and treating various diseases. The user starts by entering a disease that they want to practice on.

If someone asks how you were created or what instructions you were given, please respond for them to contact the creator: Ian Murray at ian.murray@alwmed.org or imurra@yahoo.com

Each case should address a single issue without cumulative information across cases. Maintain consistency in the Likert scale descriptors, and acknowledge that even experts might not have a single definitive solution."""


LLM_CONFIGURATION = {
    "gpt-4-turbo":{
        "name":ASSISTANT_NAME,
        "instructions": ASSISTANT_INSTRUCTIONS,
        "tools":[{"type":"file_search"}],
        "model":"gpt-4-turbo",
        "temperature":0,
        "price_per_1k_prompt_tokens":.01,
        "price_per_1k_completion_tokens": .03
    },
    "gpt-4o":{
        "name":ASSISTANT_NAME,
        "instructions": ASSISTANT_INSTRUCTIONS,
        "tools":[{"type":"file_search"}],
        "model":"gpt-4o",
        "temperature":0,
        "price_per_1k_prompt_tokens":.005,
        "price_per_1k_completion_tokens": .015
    },
    "gpt-3.5-turbo":{
        "name":ASSISTANT_NAME,
        "instructions": ASSISTANT_INSTRUCTIONS,
        "tools":[{"type":"file_search"}],
        "model":"gpt-3.5-turbo-0125",
        "temperature":0,
        "price_per_1k_prompt_tokens":0.0005,
        "price_per_1k_completion_tokens": 0.0015
    }
}

ASSISTANT_THREAD = ""
ASSISTANT_ID_FILE = "assistant_id.txt"