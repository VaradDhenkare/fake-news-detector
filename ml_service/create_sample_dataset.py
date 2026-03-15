"""
create_sample_dataset.py
------------------------
Generates a small synthetic dataset for TESTING purposes.
Creates ml_service/data/news.csv with ~300 samples.

Run:
    python create_sample_dataset.py

NOTE: Model trained on this will have lower accuracy (~75-85%).
      Replace with the real dataset later for production quality (97%+).
"""

import os
import csv
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUT_PATH = os.path.join(DATA_DIR, "news.csv")

# ── REAL news samples (headlines + body fragments) ──────────────────────────
REAL_TEMPLATES = [
    "Scientists at {org} publish findings on {topic} in peer-reviewed journal showing {fact}.",
    "The {country} government announced a new policy on {topic} after consulting {experts}.",
    "{org} reports quarterly earnings of {amount} billion, {direction} analyst expectations.",
    "WHO confirms {number} new cases of {disease} in {region} following recent outbreak.",
    "Central bank raises interest rates by {pct}% to combat rising inflation pressures.",
    "Parliament passed new legislation on {topic} with {num} votes in favor.",
    "Official data shows unemployment fell to {pct}% in {month}, the lowest in {years} years.",
    "UN climate report warns that global temperatures may rise by {num}°C by 2100.",
    "NASA successfully launches {mission} satellite to study {topic} from orbit.",
    "New study published in {journal} links {thing} to improved {health} outcomes.",
    "Stock markets closed higher on Friday as economic data showed stronger than expected growth.",
    "The Supreme Court ruled that {thing} is constitutional following a landmark case.",
    "Health ministry confirms that {vaccine} has received regulatory approval after trials.",
    "International trade agreement between {country} and {country2} signed after months of talks.",
    "Research from {university} shows that regular exercise reduces risk of {disease} by {pct}%.",
    "The central bank held rates steady citing stable inflation and solid employment figures.",
    "Government announces {amount} billion infrastructure investment plan over five years.",
    "Tech company {org} reports data breach affecting {number} million users worldwide.",
    "Flooding in {region} displaces thousands; relief operations underway says Red Cross.",
    "Election commission confirms voter turnout reached {pct}% in the general election.",
    "Ministry of health recommends updated {vaccine} booster for those above 60 years.",
    "Satellite images confirm deforestation in {region} has slowed by {pct}% this year.",
    "City council votes to expand public transit network with {num} new underground stations.",
    "Annual report shows national GDP growth of {pct}% despite global economic slowdown.",
    "Scientists discover new species of {animal} in rainforests of {region}.",
]

# ── FAKE news samples ────────────────────────────────────────────────────────
FAKE_TEMPLATES = [
    "BREAKING: {celeb} arrested for secret {crime}! Government covering it up!",
    "{country} planning to microchip all citizens by {year} — leaked documents prove it.",
    "5G towers confirmed to transmit {disease} — doctors are hiding the truth from you.",
    "EXCLUSIVE: {org} secretly adding {chemical} to {product} to control the population.",
    "{celeb} seen meeting with {group} in secret — the mainstream media won't tell you!",
    "Scientists ADMIT that {thing} causes cancer — but Big Pharma buries the study!",
    "URGENT: {country} military spotted near {region} — World War 3 is starting NOW.",
    "The {thing} you drink every day is slowly killing you, here's what they don't want you to know.",
    "DEEP STATE exposed! {org} funneling {amount} billion to {group} through secret accounts.",
    "ALERT: {government} passing secret law to ban {thing} — act NOW before it's too late.",
    "Shocking video emerges showing {celeb} performing {ritual} at private event.",
    "{country} election RIGGED — whistleblower comes forward with explosive evidence.",
    "Doctors admit that {vaccine} has caused {number} hidden deaths — media blackout!",
    "Anonymous insider reveals {org} has been lying about {topic} for {years} years.",
    "BANNED VIDEO: Watch what {government} doesn't want you to see about {topic}.",
    "EXPOSED: Chemtrails proven to contain {chemical} — pilots speak out in secret recording.",
    "Secret Pentagon document reveals aliens have been living among us since {year}.",
    "{celeb} DEAD at {age}? Hospital sources confirm — family in crisis, no official statement.",
    "You won't believe what they found in {product} — this will shock every parent.",
    "LEAKED: {country} planning to collapse global economy by selling all gold reserves.",
    "NEW WORLD ORDER confirmed: {org} meeting secretly to depopulate {region}.",
    "{thing} BANNED in {country} after it was discovered to cause permanent brain damage.",
    "Former {org} employee reveals truth about {topic} — fired for speaking out.",
    "MUST SHARE: {government} using phone apps to track your every move and thought.",
    "Billionaire {celeb} funds lab developing {thing} to control human behavior via food.",
]

# ── Template fillers ──────────────────────────────────────────────────────────
FILLERS = {
    "org":        ["WHO", "NASA", "Microsoft", "Apple", "Reuters", "the UN", "Harvard", "Oxford"],
    "topic":      ["climate change", "public health", "economic policy", "renewable energy",
                   "digital privacy", "food security", "vaccine development", "education reform"],
    "fact":       ["a 30% improvement in outcomes", "no statistically significant difference",
                   "correlation between exercise and longevity", "reduced carbon emissions"],
    "country":    ["India", "USA", "Germany", "France", "Japan", "Brazil", "Australia", "Canada"],
    "country2":   ["UK", "China", "South Korea", "Italy", "Mexico", "Singapore"],
    "experts":    ["leading economists", "public health officials", "independent scientists"],
    "amount":     ["1.2", "4.5", "18", "200", "0.8", "7.3"],
    "direction":  ["beating", "matching", "falling short of"],
    "disease":    ["COVID-19", "influenza", "measles", "dengue", "tuberculosis"],
    "region":     ["South Asia", "sub-Saharan Africa", "Eastern Europe", "Southeast Asia"],
    "pct":        ["0.25", "2.1", "3.5", "12", "28", "40", "65"],
    "num":        ["3", "7", "15", "42", "128", "300"],
    "month":      ["January", "March", "June", "September", "November"],
    "years":      ["five", "ten", "twenty", "thirty"],
    "journal":    ["Nature", "The Lancet", "Science", "JAMA", "NEJM"],
    "thing":      ["coffee", "aspirin", "regular walking", "social media use", "the new regulation"],
    "health":     ["cardiovascular", "mental", "cognitive", "immune", "long-term"],
    "vaccine":    ["COVID-19", "flu", "hepatitis B", "HPV", "meningitis"],
    "university": ["MIT", "Harvard", "Stanford", "Cambridge", "IIT"],
    "mission":    ["Artemis", "Sentinel", "Perseverance", "ISRO RISAT"],
    "number":     ["2.3 million", "500,000", "14 million", "800,000"],
    "animal":     ["frog", "beetle", "orchid", "deep-sea fish", "primate"],
    "celeb":      ["a senior politician", "a tech billionaire", "a famous actor"],
    "crime":      ["fraud scheme", "money laundering plot", "conspiracy"],
    "year":       ["2025", "2026", "2030"],
    "chemical":   ["fluoride", "graphene oxide", "nano-particles"],
    "product":    ["tap water", "processed food", "smartphones", "vaccines"],
    "group":      ["shadow government", "Illuminati", "UN globalists"],
    "government": ["the government", "deep state officials", "world leaders"],
    "ritual":     ["occult ceremony", "secret meeting", "suspicious gathering"],
    "age":        ["45", "52", "61"],
}


def fill(template):
    result = template
    for key, options in FILLERS.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            result = result.replace(placeholder, random.choice(options), 1)
        # second occurrence
        if placeholder in result:
            result = result.replace(placeholder, random.choice(options), 1)
    return result


def main():
    random.seed(42)
    rows = []

    for _ in range(200):
        rows.append({"text": fill(random.choice(REAL_TEMPLATES)), "label": "REAL"})

    for _ in range(200):
        rows.append({"text": fill(random.choice(FAKE_TEMPLATES)), "label": "FAKE"})

    random.shuffle(rows)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Sample dataset created: {OUT_PATH}")
    print(f"   Total samples : {len(rows)} (200 REAL + 200 FAKE)")
    print(f"\n⚠️  Note: This is a synthetic test dataset.")
    print(f"   Model accuracy will be ~75-85%.")
    print(f"   For production (~97%), use: python download_dataset.py --source welfake")
    print(f"\nNext step → python model_training.py")


if __name__ == "__main__":
    main()
