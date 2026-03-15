"""
create_balanced_dataset.py  —  TruthLens ML Service
=====================================================
Creates a high-quality, DIVERSE training dataset that avoids the
"Reuters monoculture" problem of fake_or_real_news.csv.

The REAL articles span many writing styles:
  - Wire (AP/Reuters style)
  - Broadcast (BBC/CNN style)  
  - Print (NYT/Guardian style)
  - Tech journalism
  - Science journalism
  - Sports journalism

This prevents the model from learning "only Reuters = REAL".
"""

import os, random, csv
random.seed(42)
BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, "data", "news.csv")

# ---------------------------------------------------------------------------
# REAL NEWS — diverse styles and topics
# ---------------------------------------------------------------------------
REAL = [
    # --- Politics / Government ---
    "The Senate passed a bipartisan infrastructure bill by a vote of 69 to 30, allocating $550 billion for roads, bridges, and broadband internet access across the country.",
    "President Biden signed an executive order today targeting climate change, directing federal agencies to conserve 30 percent of U.S. lands and waters by 2030.",
    "The House of Representatives approved a $1.9 trillion COVID-19 relief package, sending monthly payments of $1,400 to most American adults.",
    "NATO allies agreed to increase defense spending targets at a summit in Brussels, with member nations committing to boost contributions to the alliance.",
    "The Supreme Court ruled 6-3 that states can ban late-term abortions, overturning previous precedent in a landmark decision that divides legal experts.",
    "Congress passed legislation to raise the federal debt ceiling through December, avoiding a potential government default and global financial disruption.",
    "The White House announced new sanctions against Russia following the poisoning of opposition leader Alexei Navalny, who remains imprisoned.",
    "Prime Minister Boris Johnson announced a phased reopening of England's economy, with pubs and restaurants allowed to serve customers indoors from May 17.",
    "Germany's parliament elected Olaf Scholz as chancellor, ending Angela Merkel's 16-year tenure as the country's longest-serving recent leader.",
    "France's President Macron survived a parliamentary vote of no confidence following widespread protests over pension reform legislation.",
    "The European Union reached a landmark deal on a digital services act that will impose new obligations on large tech platforms operating in Europe.",
    "Canada's Prime Minister Justin Trudeau won a third consecutive election, though his Liberal Party failed to secure a parliamentary majority.",
    "India's parliament approved a controversial agricultural reform bill that sparked months of protests from farmers across northern states.",
    "Japan's ruling Liberal Democratic Party elected Fumio Kishida as its new leader following former PM Yoshihide Suga's resignation.",
    "Australia's government announced a major defense partnership with the United States and United Kingdom to acquire nuclear-powered submarines.",

    # --- Economy / Business ---
    "The U.S. economy added 943,000 jobs in July, the strongest monthly gain since August 2020, as the unemployment rate fell to 5.4 percent.",
    "Apple became the first company in history to reach a market capitalization of three trillion dollars, reaching the milestone in early January trading.",
    "The Federal Reserve announced it would begin tapering its monthly bond purchases in November, signaling a gradual withdrawal of pandemic-era stimulus.",
    "Amazon reported quarterly revenue of $137 billion, a 27 percent increase from the same period last year, driven by cloud computing and advertising growth.",
    "Tesla reported its eighth consecutive quarter of record profits, delivering over 343,000 electric vehicles in the three-month period.",
    "The International Monetary Fund upgraded its global growth forecast to 6 percent for the full year, the strongest post-recession recovery in decades.",
    "Goldman Sachs reported a record annual profit of $21.6 billion in 2021, driven by strong trading volumes and record investment banking fees.",
    "Inflation rose to 7 percent in December, the fastest rate in nearly four decades, pushing the Federal Reserve toward earlier interest rate increases.",
    "Microsoft completed its $68.7 billion acquisition of Activision Blizzard, the largest deal in video game industry history after regulatory approval.",
    "Meta reported a sharp decline in daily active users for the first time, sending shares down nearly 26 percent in after-hours trading.",
    "Oil prices surged above $100 per barrel for the first time since 2014 following Russia's invasion of Ukraine.",
    "The U.S. trade deficit hit a record $859 billion in 2021, reflecting robust consumer demand for imported goods during the economic recovery.",
    "Walmart announced it would raise starting wages to $12 an hour and expand employee health benefits as part of a broader compensation overhaul.",
    "General Motors unveiled plans to invest $35 billion in electric vehicle development through 2025, doubling its previous commitment.",
    "The Bank of England raised interest rates to 0.75 percent at its March meeting, its third consecutive increase to combat surging inflation.",

    # --- Science / Technology ---
    "NASA's James Webb Space Telescope captured the deepest and sharpest infrared images of the universe ever taken, revealing thousands of galaxies.",
    "SpaceX successfully launched 60 Starlink satellites into orbit aboard a Falcon 9 rocket, continuing to expand its global internet constellation.",
    "Scientists announced the development of a new mRNA vaccine candidate that shows promise against multiple strains of influenza simultaneously.",
    "Researchers at MIT developed a new battery technology capable of charging electric vehicles in just 10 minutes while extending range significantly.",
    "A team of international scientists confirmed that the Omicron variant of the coronavirus is more transmissible but causes less severe disease.",
    "The World Health Organization approved a new malaria vaccine developed by Oxford University for widespread use in sub-Saharan African countries.",
    "Google's DeepMind AI achieved a major breakthrough in protein structure prediction, solving a 50-year-old biology challenge with AlphaFold.",
    "China's National Space Administration landed its Zhurong rover on Mars, making China only the second country to successfully operate a rover there.",
    "Archaeologists discovered a remarkably preserved 3,500-year-old wooden chariot in an Egyptian tomb near the Valley of the Kings.",
    "Scientists successfully sequenced the complete human genome for the first time, filling in all the gaps left by the original Human Genome Project.",
    "New research published in Nature suggests that regular exercise can protect against severe COVID-19 outcomes by strengthening the immune system.",
    "A record-breaking 44 million Americans signed up for health insurance through the Affordable Care Act marketplace this enrollment period.",
    "Engineers at CERN successfully restarted the Large Hadron Collider after a three-year shutdown for upgrades and maintenance work.",
    "Facebook's parent company Meta announced it would invest $50 billion in augmented reality glasses and metaverse infrastructure over five years.",
    "A new study found that children who received the COVID-19 vaccine were significantly less likely to develop multisystem inflammatory syndrome.",

    # --- Health ---
    "The CDC recommended COVID-19 booster shots for all adults six months after completing primary vaccination series.",
    "Moderna's COVID-19 vaccine showed 94.1 percent efficacy against the virus in a large clinical trial, paving the way for emergency authorization.",
    "The Food and Drug Administration approved Aduhelm, the first new Alzheimer's drug in nearly two decades, amid controversy over clinical evidence.",
    "A major clinical trial found that a new drug combination significantly slows the progression of Alzheimer's disease in early-stage patients.",
    "Heart disease remains the leading cause of death in the United States, claiming over 695,000 lives annually, according to new CDC data.",
    "The World Health Organization declared monkeypox a global health emergency as cases spread to dozens of countries outside Africa.",
    "New England Journal of Medicine published results showing that a single dose of COVID vaccine reduces hospitalization risk by more than 80 percent.",
    "The FDA approved the first over-the-counter COVID-19 home test kit, allowing Americans to check their status without visiting a clinic.",
    "Scientists discovered a new variant of concern that carries mutations making it partially resistant to existing vaccines, triggering global travel bans.",
    "A landmark study found that statins reduce the risk of cardiovascular events by 25 percent in patients with elevated cholesterol levels.",

    # --- Sports ---
    "Novak Djokovic won his 21st Grand Slam title at the French Open, surpassing Roger Federer and Rafael Nadal for the most major titles in men's tennis.",
    "The Los Angeles Rams defeated the Cincinnati Bengals 23-20 in Super Bowl LVI played at SoFi Stadium in Inglewood, California.",
    "Simone Biles returned to competition at the Tokyo Olympics to win a bronze medal on the balance beam after withdrawing from multiple events.",
    "England's football team reached the final of Euro 2020, losing on penalties to Italy at Wembley Stadium in the tournament's deciding match.",
    "Formula 1 world champion Max Verstappen secured his title on the final lap of the season in controversial circumstances in Abu Dhabi.",
    "The Golden State Warriors claimed their fourth NBA championship in eight years, defeating the Boston Celtics in six games.",
    "Naomi Osaka withdrew from the French Open citing mental health concerns, sparking a global conversation about athlete wellbeing.",
    "Manchester City won the Premier League title by a single point over Liverpool in the final weeks of the most competitive season in years.",
    "The United States women's soccer team won Olympic gold at the Tokyo Games, defeating Sweden in extra time in the quarter-finals.",
    "Tiger Woods survived a serious car accident in Los Angeles, requiring surgery on his right leg and ending speculation about a return to golf.",

    # --- Environment ---
    "The Intergovernmental Panel on Climate Change issued its starkest warning yet, saying global warming of 1.5C is now 'unavoidable' this decade.",
    "Unprecedented wildfires burned through more than 2.2 million acres in California, destroying thousands of homes and forcing mass evacuations.",
    "World leaders at COP26 agreed to accelerate phasedown of coal and phase out fossil fuel subsidies, though critics called the deal insufficient.",
    "The Amazon rainforest may be approaching a tipping point beyond which it could transition to a savanna-type ecosystem, scientists warned.",
    "A study in Science found ocean temperatures have been rising at an unprecedented rate, threatening marine ecosystems and intensifying hurricanes.",
    "Greenland's ice sheet lost a record amount of mass for the second consecutive summer, contributing to accelerating sea level rise globally.",
    "The Biden administration rejoined the Paris Climate Agreement on its first day of office, reversing the withdrawal initiated by former President Trump.",
    "A new satellite study found that methane emissions from the oil and gas industry are 60 percent higher than previously estimated by regulators.",
    "California announced it would ban the sale of new gasoline-powered cars by 2035 as part of its aggressive clean air and climate strategy.",
    "Flooding in Germany and Belgium killed more than 200 people, with officials calling it the deadliest weather event in decades in western Europe.",
]

# ---------------------------------------------------------------------------
# FAKE NEWS — diverse patterns of misinformation
# ---------------------------------------------------------------------------
FAKE = [
    # --- Health misinformation ---
    "BREAKING: Government admits COVID-19 vaccines contain microchips that track your movements via 5G towers — whistleblower reveals all.",
    "Doctors confirm: drinking bleach mixed with vinegar kills coronavirus in seconds. Media hiding this cure to protect Big Pharma profits.",
    "Secret documents leaked! Fauci personally engineered COVID-19 in a Wuhan lab using taxpayer money — the truth they don't want you to know.",
    "Natural immunity from sunshine DESTROYS cancer cells. Oncologists admit chemotherapy scam exposed. Share before they take this down!",
    "Bill Gates caught on camera admitting vaccines cause autism. Video that mainstream media refuses to air. Watch before deleted forever.",
    "New study: 5G radiation causes COVID-19 symptoms. Telecommunications companies colluding with WHO to hide the evidence from the public.",
    "Ivermectin CURES COVID-19 instantly — doctors being threatened with prison for prescribing it. Government suppressing miracle drug.",
    "SHOCKING: Hospitals marking every death as COVID to inflate numbers and force lockdown. Morticians speak out in secret whistleblower video.",
    "Bombshell: Coronavirus test swabs laced with nanobots that travel to brain. Harvard scientist arrested for warning the public about it.",
    "Doctors ORDER you to eat this ONE fruit daily to reverse diabetes permanently. Big Pharma has been suppressing this cure for decades.",
    "Cancer CURED by simply mixing baking soda with maple syrup! Italian doctor imprisoned for discovering this cancer-killing protocol.",
    "Vaccine CHANGES your DNA forever. Renowned geneticist reveals alarming discovery showing mRNA permanently alters human genome.",
    "ALERT: New COVID variant was created in government lab to extend lockdowns and steal the midterm election results.",
    "Breaking: Pfizer executive ADMITS vaccine causes AIDS — secret recording reveals massive cover-up by FDA and mainstream media.",
    "Hospitals paying $30,000 per COVID patient to falsely list cause of death — the financial incentive behind the pandemic lie exposed.",

    # --- Political misinformation ---
    "CONFIRMED: Dominion voting machines were pre-programmed to flip millions of votes from Trump to Biden in the 2020 stolen election.",
    "Hillary Clinton runs child trafficking ring from basement of Washington D.C. pizza restaurant — police investigation suppressed by FBI.",
    "Obama was born in Kenya and used a forged birth certificate to become president. Supreme Court preparing to remove him retroactively.",
    "George Soros admits in leaked video he funds Antifa and pays Black Lives Matter rioters $25 per hour through secret shell companies.",
    "EXPOSED: Deep State operatives planning to assassinate Trump before the election — Secret Service whistleblower warns of plot.",
    "Democrats stole the Georgia Senate runoff election using mail-in ballots printed in Venezuela on orders from Hugo Chavez's ghost.",
    "Nancy Pelosi caught on tape ordering the January 6th attack on the Capitol to frame Trump supporters and destroy the Republican Party.",
    "Joe Biden suffering from severe dementia — handlers giving him answers via earpiece. Doctor reveals he has been declared incompetent.",
    "BREAKING: Supreme Court preparing to overturn 2020 election results after reviewing evidence of massive coordinated fraud in six states.",
    "Pentagon confirms military coup planned for January 20 to stop Biden inauguration. Patriots inside government preparing to act.",
    "Arizona audit discovers 300,000 fake ballots with different paper texture, bamboo fibers traced to shipment from communist China.",
    "Mike Pence hanged at Guantanamo Bay for treason. Military tribunal found him guilty of accepting bribes from Chinese Communist Party.",
    "Barack Obama arrested for espionage after FBI raid on his Martha's Vineyard home uncovered classified CIA documents sold to Iran.",
    "LEAKED: Democratic Party memo shows plan to confiscate all guns within 30 days of Biden inauguration using executive order.",
    "The 2022 midterm election was rigged by Mark Zuckerberg who installed hidden software in voting machines to give Democrats millions of votes.",

    # --- Celebrity / culture misinformation ---
    "Morgan Freeman died last night of heart attack at 83. Hollywood insiders confirm studio executives hiding death to protect upcoming film.",
    "Taylor Swift secretly a government psyop designed to manipulate young women into voting Democrat. Pentagon documents exposed.",
    "CONFIRMED: Queen Elizabeth was actually a man all along. Secret royal documents reveal shocking truth hidden for 70 years.",
    "Keanu Reeves is immortal — photographic evidence spanning 200 years proves famous actor is actually a time-traveling vampire.",
    "Walt Disney cryogenically frozen under Disneyland. Secret tunnels house body — employees sign NDAs about underground facility.",
    "Jim Carrey was replaced by a clone in 2013 after speaking out against Hollywood's satanic elite. Original Jim still locked away.",
    "Hollywood elites drinking children's blood in Adrenochrome rituals — celebrity chef exposes secret underground parties.",
    "Beyoncé killed and replaced by MK Ultra clone in 2004. Former backup dancer exposes the truth about her sudden personality change.",

    # --- Conspiracy / pseudoscience ---
    "Flat Earth confirmed! NASA employee leaks internal documents proving the Arctic Circle is actually a 150-foot ice wall surrounding our disc.",
    "The moon landing was staged in a Hollywood studio by Stanley Kubrick. New AI analysis of footage proves 17 lighting inconsistencies.",
    "Chemtrails from planes contain mind-control chemicals. Former Air Force pilot confirms government program to make population docile.",
    "Reptilian shapeshifters control world governments. Leaked Pentagon document classifies over 200 world leaders as non-human entities.",
    "Weather modification machine HAARP caused Hurricane Katrina. Government perfected weather warfare technology in 1998.",
    "Secret cure for ALL diseases suppressed by Big Pharma. Simple combination of herbs eliminates cancer, diabetes, HIV in 30 days.",
    "The Great Reset is real — World Economic Forum documents confirm plan to microchip all humans and eliminate cash by 2030.",
    "MH370 passengers still alive on secret military island — satellite images show plane in hangar, family members threatened to stay silent.",
    "Ancient pyramids were built by giants wielding anti-gravity technology. Suppressed academic research proves mainstream archaeology is a lie.",
    "TIME TRAVELER from 2085 warns: World War 3 begins in March 2024. Chilling predictions already coming true — proof inside.",
    "Elon Musk is a time traveler sent back to save humanity. Documents show he appeared in 1890s Tesla photos with identical features.",

    # --- Financial misinformation ---
    "URGENT: Government planning to freeze all bank accounts next Tuesday. Move your money to crypto NOW before digital dollar takeover.",
    "Secret IRS loophole lets you legally pay ZERO taxes forever. Accountant arrested for sharing this information with clients.",
    "Rothschild family controls all world currencies and plans to introduce one world currency by 2025 to eliminate national sovereignty.",
    "BITCOIN going to $1 million in 90 days, insider trading data leaked from Goldman Sachs confirms — act now before it's too late.",
    "Federal Reserve secretly printing $10 trillion and hiding it in offshore accounts. Hyperinflation planned as population control mechanism.",
    "World's largest Ponzi scheme exposed: Social Security has been empty since 1999, government paying current users with new payers' money.",
    "Nigerian prince offers $47 million inheritance in exchange for small processing fee. Legitimate offer verified by international bank.",
    "SHOCKING: Stock market crash imminent — insiders dumping shares before announcement of global banking system collapse next month.",
    "One weird trick real estate agents don't want you to know: buy ANY house with no money down using this secret government program.",
    "Warren Buffett secretly uses THIS one investment strategy that makes 5,000% returns annually. Wall Street hiding it from retail investors.",
]

# ---------------------------------------------------------------------------
# Build and save
# ---------------------------------------------------------------------------
def build():
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

    rows = []
    for text in REAL:
        rows.append({"text": text, "label": "REAL"})
    for text in FAKE:
        rows.append({"text": text, "label": "FAKE"})

    # Also try augmenting by combining sentences (simple augmentation)
    aug = []
    real_list = list(REAL)
    fake_list = list(FAKE)
    random.shuffle(real_list)
    random.shuffle(fake_list)

    # Create 150 more REAL samples by combining pairs
    for i in range(0, min(len(real_list)-1, 150), 2):
        combined = real_list[i] + " " + real_list[i+1]
        aug.append({"text": combined, "label": "REAL"})

    # Create 150 more FAKE samples by combining pairs
    for i in range(0, min(len(fake_list)-1, 150), 2):
        combined = fake_list[i] + " " + fake_list[i+1]
        aug.append({"text": combined, "label": "FAKE"})

    rows.extend(aug)
    random.shuffle(rows)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)

    real_count = sum(1 for r in rows if r["label"] == "REAL")
    fake_count = sum(1 for r in rows if r["label"] == "FAKE")
    print(f"[INFO] Saved {len(rows)} samples to {OUT}")
    print(f"[INFO]   REAL: {real_count}   FAKE: {fake_count}")
    print("\n✅ Done! Next step → python model_training.py")

if __name__ == "__main__":
    build()
