"""
LinkedIn Optimizer — generates a complete profile rewrite based on user profile.
Run: python run.py linkedin
"""

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, USER_PROFILE, BASE_RESUME, LINKEDIN_OUT

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)

LINKEDIN_PROMPT = """
You are an expert LinkedIn profile optimizer for the AI + Healthcare sector.
Your client is a Medical Doctor from Colombia transitioning deeper into remote,
tech-forward roles (AI operations, clinical informatics, prompt engineering).

## Client Profile
{profile}

## Client's Base Resume
{resume}

## The Assignment
Write a complete LinkedIn profile optimization guide for this client.
Format your response in clean Markdown. Include the following sections exactly:

# LinkedIn Profile Optimization: AI + Healthcare Focus

## 1. Headline Options
Provide 3 excellent, ATS-friendly headlines. They must bridge the MD background
with AI/Tech capabilities without sounding like a traditional practicing physician.
(Formula: Role | Niche | Value Proposition)

## 2. About Section (Summary)
Write a compelling, first-person narrative (200-300 words).
- Hook: Start with a strong statement about the intersection of medicine and AI.
- Body: Tell the story of moving from clinical understanding to system prompts and automation.
- Conclusion: What you are looking for next (remote AI/healthcare roles) and an invitation to connect.

## 3. Experience Rewrite
Rewrite the standard resume bullets into LinkedIn-style storytelling bullets for their
top 3 roles starting with the Intake Operations Manager and Freelance AI Systems roles.
Focus heavily on the 5% denial rate outcome and the WhatsApp AI bot.

## 4. Top 15 Skills to Add
List the exact skill names they should pin to their profile, prioritized.
(Mix of Healthcare IT, AI/LLMs, and soft skills).

## 5. Featured Section Recommendations
What 2-3 specific items should they add to their "Featured" carousel? (e.g., screenshots
of the WhatsApp bot, a post about prompt engineering, etc.)

## 6. Connection Strategy: Who to Target
List 3 types of job titles the client should actively send connection requests to
(e.g., "Director of Clinical Informatics at [AI Startup]").
"""

def generate_linkedin_rewrite():
    print("[LinkedIn] Generating profile rewrite. This takes about 15 seconds...")
    try:
        resume_text = BASE_RESUME.read_text(encoding="utf-8") if BASE_RESUME.exists() else "No resume provided."
        
        prompt = LINKEDIN_PROMPT.format(
            profile=USER_PROFILE,
            resume=resume_text
        )
        
        response = _model.generate_content(prompt)
        content = response.text.strip()
        
        LINKEDIN_OUT.parent.mkdir(parents=True, exist_ok=True)
        LINKEDIN_OUT.write_text(content, encoding="utf-8")
        
        print(f"\n[LinkedIn] Success! Your profile rewrite is ready at:")
        print(f"  → {LINKEDIN_OUT}")
        print("\nOpen this file, review the suggestions, and manually update your LinkedIn profile.")
        
    except Exception as e:
        print(f"[LinkedIn] Generation failed: {e}")

if __name__ == "__main__":
    generate_linkedin_rewrite()
