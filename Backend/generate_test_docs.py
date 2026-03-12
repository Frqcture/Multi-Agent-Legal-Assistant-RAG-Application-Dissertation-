"""
Generate 5 synthetic, anonymised legal case file PDFs for RAG evaluation.
Each document contains verifiable facts for ground-truth testing.
"""

import os
from fpdf import FPDF


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "TestDocuments")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class LegalPDF(FPDF):
    """Helper for consistent legal document formatting."""

    def header(self):
        if hasattr(self, "_doc_title"):
            self.set_font("Helvetica", "B", 9)
            self.cell(0, 5, self._doc_title, align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title(self, title):
        self._doc_title = title
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(4)

    def add_subtitle(self, text):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_body(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def add_bold_line(self, text):
        self.set_font("Helvetica", "B", 10)
        self.multi_cell(0, 5, text)
        self.ln(1)


def doc1_thompson_v_meridian():
    """Case 1: Construction contract dispute -- Thompson v Meridian Construction Ltd."""
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Page 1 ---
    pdf.add_page()
    pdf.add_title("CONFIDENTIAL CLIENT FILE")
    pdf.add_subtitle("Thompson v Meridian Construction Ltd")
    pdf.add_body(
        "File Reference: TC/2025/0892\n"
        "Date Opened: 14 March 2025\n"
        "Fee Earner: Ms. Angela Barton, Senior Associate\n"
        "Client: Mr. James Thompson\n"
        "Opponent: Meridian Construction Ltd (Company No. 08451723)"
    )
    pdf.add_subtitle("1. Client Background")
    pdf.add_body(
        "Mr. James Thompson, aged 54, resides at 12 Oakfield Gardens, Bristol, BS8 2LQ. "
        "Mr. Thompson is a retired civil engineer who purchased the property in January 2019 "
        "for GBP 425,000. He instructed this firm on 14 March 2025 regarding defective building "
        "works carried out by Meridian Construction Ltd at his property."
    )
    pdf.add_subtitle("2. Summary of Facts")
    pdf.add_body(
        "On 3 June 2024, Mr. Thompson entered into a written construction contract with Meridian "
        "Construction Ltd for the construction of a two-storey rear extension to his property. The "
        "total contract price was GBP 187,500, payable in four staged instalments. The contract "
        "specified a completion date of 15 November 2024.\n\n"
        "The four payment instalments were agreed as follows:\n"
        "  - Stage 1 (Foundations): GBP 46,875 -- paid 10 June 2024\n"
        "  - Stage 2 (Shell / Superstructure): GBP 46,875 -- paid 5 August 2024\n"
        "  - Stage 3 (First Fix): GBP 46,875 -- paid 2 October 2024\n"
        "  - Stage 4 (Completion / Handover): GBP 46,875 -- withheld by client\n\n"
        "Mr. Thompson paid the first three instalments totalling GBP 140,625. He withheld the "
        "final instalment of GBP 46,875 after identifying serious defects during a pre-handover "
        "inspection on 18 November 2024."
    )

    # --- Page 2 ---
    pdf.add_page()
    pdf.add_subtitle("3. Schedule of Defects")
    pdf.add_body(
        "A chartered surveyor, Mr. David Hargreaves MRICS, was instructed to prepare an "
        "independent defects report dated 9 January 2025. The report identified the following "
        "defects:\n\n"
        "3.1 Structural Cracking: Significant cracking (exceeding 5mm in width) was observed "
        "in the load-bearing wall at ground floor level on the eastern elevation, indicating "
        "potential foundation movement.\n\n"
        "3.2 Roof Defects: The flat roof membrane was improperly installed with inadequate falls, "
        "resulting in persistent water ponding. Multiple areas of the roof covering showed early "
        "signs of delamination.\n\n"
        "3.3 Drainage: The below-ground drainage was found to be non-compliant with Building "
        "Regulations Approved Document H. Specifically, the foul drainage run had insufficient "
        "gradient (1:120 instead of minimum 1:80) and two inspection chambers lacked proper "
        "benching.\n\n"
        "3.4 Electrical Installation: The consumer unit did not comply with BS 7671 (18th Edition "
        "Wiring Regulations). Fourteen circuits were identified without adequate RCD protection.\n\n"
        "3.5 Window Installation: Three of the six windows installed in the extension were found "
        "to have missing or defective cavity trays, creating a risk of moisture penetration."
    )
    pdf.add_subtitle("4. Estimated Remediation Costs")
    pdf.add_body(
        "Mr. Hargreaves estimated the total cost of remediation works at GBP 74,300, broken down "
        "as follows:\n"
        "  - Structural repairs (underpinning and crack stabilisation): GBP 28,500\n"
        "  - Roof replacement: GBP 14,200\n"
        "  - Drainage remediation: GBP 11,800\n"
        "  - Electrical rewiring: GBP 8,600\n"
        "  - Window cavity tray installation: GBP 5,400\n"
        "  - Supervision and contingency (8%): GBP 5,800\n\n"
        "Total estimated remediation: GBP 74,300"
    )

    # --- Page 3 ---
    pdf.add_page()
    pdf.add_subtitle("5. Pre-Action Correspondence")
    pdf.add_body(
        "A Letter Before Action was sent to Meridian Construction Ltd on 22 January 2025 pursuant "
        "to the Pre-Action Protocol for Construction and Engineering Disputes. The letter set out "
        "the schedule of defects and demanded remediation within 28 days or, alternatively, payment "
        "of GBP 74,300 as damages.\n\n"
        "Meridian Construction Ltd responded on 14 February 2025 through their solicitors, Blake "
        "Farnsworth LLP. In their response, Meridian denied liability for the structural cracking "
        "(attributing it to pre-existing ground conditions) and the drainage defects (claiming these "
        "were completed to the specification agreed with Mr. Thompson's architect). Meridian accepted "
        "liability for the roof defects and the window cavity trays, offering GBP 19,600 in full and "
        "final settlement.\n\n"
        "Mr. Thompson rejected this offer on 3 March 2025 as it fell significantly short of the "
        "surveyor's total remediation estimate."
    )
    pdf.add_subtitle("6. Legal Analysis")
    pdf.add_body(
        "The claim is founded in breach of contract and, in the alternative, negligence. The "
        "relevant statutory framework includes:\n"
        "  - Supply of Goods and Services Act 1982, s.13 (implied term of reasonable care and skill)\n"
        "  - Defective Premises Act 1972, s.1 (duty to build dwellings properly)\n"
        "  - Building Act 1984 and associated Building Regulations 2010\n\n"
        "The limitation period for breach of contract is 6 years from the date of breach (Limitation "
        "Act 1980, s.5). As the contract was entered on 3 June 2024, the claim is well within time.\n\n"
        "Mr. Thompson's claim totals GBP 74,300 in remediation costs, plus GBP 3,200 in alternative "
        "accommodation costs incurred during the period when the property was uninhabitable due to the "
        "roof leaks (December 2024 to January 2025), bringing the total claim to GBP 77,500."
    )

    # --- Page 4 ---
    pdf.add_page()
    pdf.add_subtitle("7. Recommended Next Steps")
    pdf.add_body(
        "7.1 Issue proceedings in the Technology and Construction Court (TCC) if no satisfactory "
        "settlement is reached within 14 days of the date of this file note.\n\n"
        "7.2 Consider instructing a structural engineer to provide a supplementary report on the "
        "foundation cracking to rebut Meridian's defence of pre-existing ground conditions.\n\n"
        "7.3 Obtain quotations from two independent contractors for the remediation works to "
        "corroborate Mr. Hargreaves' estimate.\n\n"
        "7.4 Explore the possibility of adjudication under the Housing Grants, Construction and "
        "Regeneration Act 1996 as an alternative to litigation."
    )
    pdf.add_subtitle("8. Costs Estimate")
    pdf.add_body(
        "An initial costs estimate for pursuing the claim through to trial in the TCC is "
        "GBP 35,000 to GBP 45,000 (excluding VAT and disbursements). Given the claim value of "
        "GBP 77,500, the proportionality of costs should be kept under review."
    )

    path = os.path.join(OUTPUT_DIR, "Thompson_v_Meridian_Construction.pdf")
    pdf.output(path)
    print(f"Created: {path}")


def doc2_williams_employment():
    """Case 2: Employment tribunal -- Williams unfair dismissal."""
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Page 1 ---
    pdf.add_page()
    pdf.add_title("CONFIDENTIAL CLIENT FILE")
    pdf.add_subtitle("Williams v Ashford Logistics PLC -- Employment Tribunal Claim")
    pdf.add_body(
        "File Reference: SW/2025/1104\n"
        "Date Opened: 28 January 2025\n"
        "Fee Earner: Mr. Richard Owens, Partner\n"
        "Client: Ms. Sarah Williams\n"
        "Respondent: Ashford Logistics PLC"
    )
    pdf.add_subtitle("1. Client Details")
    pdf.add_body(
        "Ms. Sarah Williams, aged 38, resides at 7 Birchwood Avenue, Manchester, M14 5RG. "
        "Ms. Williams holds a BSc in Supply Chain Management from the University of Manchester (2009). "
        "She was employed by Ashford Logistics PLC as a Regional Operations Manager from 2 September "
        "2018 until her summary dismissal on 17 December 2024. Her annual salary at the date of "
        "dismissal was GBP 62,000 with an additional performance bonus of up to 15% (approximately "
        "GBP 9,300 per annum)."
    )
    pdf.add_subtitle("2. Employment History")
    pdf.add_body(
        "Ms. Williams joined Ashford Logistics PLC on 2 September 2018 as an Operations Coordinator "
        "(Grade 5). She was promoted to Senior Operations Coordinator (Grade 6) on 1 April 2020. On "
        "15 January 2022, she was promoted to Regional Operations Manager (Grade 8), the position "
        "she held until her dismissal. Throughout her employment, Ms. Williams received consistently "
        "positive performance appraisals. Her most recent appraisal, dated 30 June 2024, rated her "
        "as 'Exceeds Expectations' with an overall score of 4.2 out of 5.0.\n\n"
        "Her total length of continuous service at the date of dismissal was 6 years and 3 months."
    )

    # --- Page 2 ---
    pdf.add_page()
    pdf.add_subtitle("3. Circumstances of Dismissal")
    pdf.add_body(
        "On 28 November 2024, Ms. Williams raised a formal grievance with Ashford's HR department "
        "regarding the conduct of her line manager, Mr. Paul Greyson (Director of Northern Operations). "
        "The grievance alleged:\n"
        "  (a) Persistent bullying behaviour, including shouting and public humiliation in team "
        "meetings on three documented occasions (4 October, 18 October, and 11 November 2024);\n"
        "  (b) Failure to follow the company's flexible working policy after Ms. Williams requested "
        "a modified schedule to care for her elderly mother; and\n"
        "  (c) Exclusion from a senior leadership development programme for which she met all "
        "published eligibility criteria.\n\n"
        "On 10 December 2024, before the grievance investigation was concluded, Ms. Williams was "
        "invited to a disciplinary hearing. The stated grounds were 'gross misconduct' relating to "
        "an alleged unauthorised disclosure of confidential client shipping schedules. On 17 December "
        "2024, Ms. Williams was summarily dismissed."
    )
    pdf.add_subtitle("4. Evidence in Support of Claim")
    pdf.add_body(
        "4.1 The alleged confidential disclosure concerned an email Ms. Williams sent on 15 November "
        "2024 to a client contact (Mr. Derek Tan, Logistics Manager at Briarfield Retail Ltd) "
        "containing an updated delivery schedule. Ms. Williams states this was sent in the ordinary "
        "course of business and was expressly authorised by her previous line manager, Ms. Fiona West, "
        "who left the company in August 2024.\n\n"
        "4.2 Three colleagues -- Ms. Karen Hughes, Mr. Tariq Rashid, and Ms. Nina Volkov -- have "
        "confirmed in writing that sharing delivery schedules with key clients was standard practice "
        "within the Northern Operations division.\n\n"
        "4.3 The disciplinary investigation file (obtained via subject access request under UK GDPR, "
        "Article 15) reveals that Mr. Greyson personally referred the matter for disciplinary action "
        "on 5 December 2024, five working days after the grievance was submitted against him. The "
        "investigation was conducted by Ms. Laura Beckett (HR Business Partner) who reported to "
        "Mr. Greyson."
    )

    # --- Page 3 ---
    pdf.add_page()
    pdf.add_subtitle("5. Heads of Claim")
    pdf.add_body(
        "Ms. Williams brings the following claims before the Employment Tribunal:\n\n"
        "5.1 Unfair Dismissal (Employment Rights Act 1996, s.94): The dismissal was both "
        "substantively and procedurally unfair. The alleged conduct did not constitute gross "
        "misconduct, and the dismissal was a retaliatory response to the protected grievance.\n\n"
        "5.2 Automatic Unfair Dismissal (ERA 1996, s.103A): The principal reason for dismissal "
        "was that Ms. Williams made a protected disclosure (whistleblowing) within her grievance "
        "regarding Mr. Greyson's failure to comply with company policies.\n\n"
        "5.3 Detriment for Making a Protected Disclosure (ERA 1996, s.47B): The disciplinary "
        "proceedings were initiated as a detriment for raising the grievance.\n\n"
        "5.4 Breach of Contract: Summary dismissal without notice, entitling Ms. Williams to "
        "damages equivalent to her contractual notice period of 12 weeks (GBP 14,307.69)."
    )
    pdf.add_subtitle("6. Schedule of Loss")
    pdf.add_body(
        "Basic Award: GBP 6,510 (6 complete years x 1 week's pay capped at GBP 1,085)\n"
        "Compensatory Award (estimated 12 months):\n"
        "  - Loss of earnings (12 months x GBP 5,166.67): GBP 62,000\n"
        "  - Loss of bonus: GBP 9,300\n"
        "  - Loss of pension contributions (6% employer): GBP 3,720\n"
        "  - Loss of statutory rights: GBP 500\n"
        "Notice pay (12 weeks): GBP 14,307.69\n"
        "Injury to feelings (Vento middle band): GBP 15,000 to GBP 28,000\n\n"
        "Total estimated claim value: GBP 111,337.69 to GBP 124,337.69\n\n"
        "The ACAS Early Conciliation certificate reference is EC/2025/00471, issued on 20 January 2025. "
        "The ET1 must be submitted by 17 March 2025."
    )

    # --- Page 4 ---
    pdf.add_page()
    pdf.add_subtitle("7. Respondent's Likely Defence")
    pdf.add_body(
        "It is anticipated that Ashford Logistics PLC will argue:\n"
        "  (a) The disclosure to Briarfield Retail Ltd constituted a genuine breach of the company's "
        "Information Security Policy (Version 3.2, July 2023);\n"
        "  (b) The timing of the disciplinary action relative to the grievance was coincidental;\n"
        "  (c) The investigation was conducted independently by HR.\n\n"
        "These defences are undermined by the evidence that Mr. Greyson personally initiated the "
        "disciplinary referral and that Ms. Beckett's line of reporting created a conflict of interest. "
        "Furthermore, the Respondent's own policy (Section 4.7) permits sharing of operational "
        "schedules with contracted clients under existing service level agreements."
    )
    pdf.add_subtitle("8. Risk Assessment")
    pdf.add_body(
        "Prospects of success on the unfair dismissal claim are assessed at 75-80%. The automatic "
        "unfair dismissal / whistleblowing claim carries a higher evidential burden but the "
        "circumstantial evidence of causation (timing, conflict of interest) is strong -- prospects "
        "estimated at 60-65%.\n\n"
        "Recommendation: Proceed with ET1 submission and seek judicial mediation at the preliminary "
        "hearing stage."
    )

    path = os.path.join(OUTPUT_DIR, "Williams_v_Ashford_Logistics_Employment.pdf")
    pdf.output(path)
    print(f"Created: {path}")


def doc3_chen_estate():
    """Case 3: Probate / contested will -- Estate of Robert Chen."""
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Page 1 ---
    pdf.add_page()
    pdf.add_title("CONFIDENTIAL CLIENT FILE")
    pdf.add_subtitle("In the Matter of the Estate of Robert David Chen (Deceased)")
    pdf.add_body(
        "File Reference: RC/2025/0563\n"
        "Date Opened: 7 February 2025\n"
        "Fee Earner: Ms. Priya Mehta, Associate Solicitor\n"
        "Client: Ms. Emily Chen (Executor and Beneficiary)\n"
        "Deceased: Mr. Robert David Chen (Date of Death: 19 December 2024)"
    )
    pdf.add_subtitle("1. Background")
    pdf.add_body(
        "Mr. Robert David Chen died on 19 December 2024 at the age of 71 at Queen Elizabeth Hospital, "
        "Birmingham. Cause of death was recorded as pancreatic cancer. He was a retired consultant "
        "orthopaedic surgeon who had practised at the Royal Orthopaedic Hospital, Birmingham for "
        "32 years.\n\n"
        "Mr. Chen was survived by three children:\n"
        "  (a) Ms. Emily Chen, aged 42, of 9 Sycamore Lane, Edgbaston, Birmingham, B15 3LR "
        "(the Executor);\n"
        "  (b) Mr. Daniel Chen, aged 39, of 145 Harbourside, Auckland, New Zealand; and\n"
        "  (c) Ms. Laura Chen-Morrison, aged 36, of 28 Regents Park Road, London, NW1 7TL.\n\n"
        "Mr. Chen's wife, Mrs. Margaret Chen (nee Harrington), predeceased him on 4 April 2021."
    )

    # --- Page 2 ---
    pdf.add_page()
    pdf.add_subtitle("2. The Will")
    pdf.add_body(
        "Mr. Chen executed his last Will and Testament on 15 March 2023, witnessed by Dr. Simon "
        "Bradshaw and Mrs. Catherine Yates, both of whom have confirmed their attestation.\n\n"
        "The material provisions of the Will are as follows:\n\n"
        "Clause 3: Appointment of Executor -- Ms. Emily Chen is appointed sole executor and trustee.\n\n"
        "Clause 5: Specific Legacies:\n"
        "  (a) GBP 50,000 to Macmillan Cancer Support (Registered Charity No. 261017);\n"
        "  (b) GBP 25,000 to the Royal Orthopaedic Hospital Charitable Fund;\n"
        "  (c) The collection of Chinese jade figurines to the Birmingham Museum and Art Gallery.\n\n"
        "Clause 6: Residuary Estate -- to be divided equally between the three children "
        "(Emily, Daniel, and Laura) in equal one-third shares.\n\n"
        "Clause 7: The property at 9 Sycamore Lane, Edgbaston is specifically devised to Ms. Emily "
        "Chen, subject to her paying any outstanding mortgage (currently GBP 62,000 remaining)."
    )
    pdf.add_subtitle("3. Estate Valuation")
    pdf.add_body(
        "A preliminary estate valuation has been prepared as follows:\n\n"
        "Real Property:\n"
        "  - 9 Sycamore Lane, Edgbaston (estimated value): GBP 785,000\n"
        "  - 14 Windermere Cottages, Lake District (holiday let): GBP 340,000\n\n"
        "Financial Assets:\n"
        "  - Barclays current account: GBP 23,400\n"
        "  - Scottish Widows pension fund: GBP 312,000\n"
        "  - Hargreaves Lansdown ISA portfolio: GBP 187,500\n"
        "  - NS&I Premium Bonds: GBP 50,000\n\n"
        "Personal Property:\n"
        "  - Jade figurine collection (Sotheby's valuation): GBP 95,000\n"
        "  - 2022 Mercedes E-Class: GBP 28,000\n"
        "  - Other personal effects: GBP 15,000\n\n"
        "Gross Estate: GBP 1,835,900\n"
        "Less Liabilities:\n"
        "  - Outstanding mortgage: GBP 62,000\n"
        "  - Credit card debts: GBP 4,300\n"
        "  - Funeral expenses: GBP 6,800\n"
        "Net Estate: GBP 1,762,800"
    )

    # --- Page 3 ---
    pdf.add_page()
    pdf.add_subtitle("4. Inheritance Tax Position")
    pdf.add_body(
        "The nil-rate band (NRB) is GBP 325,000. The transferable nil-rate band (TNRB) from "
        "Mrs. Margaret Chen's unused allowance adds a further GBP 325,000, giving a combined "
        "NRB of GBP 650,000.\n\n"
        "The residence nil-rate band (RNRB) of GBP 175,000 applies as the main residence passes "
        "to a direct descendant (Emily). The transferable RNRB from Margaret's estate adds a "
        "further GBP 175,000, giving a combined RNRB of GBP 350,000.\n\n"
        "Total available nil-rate bands: GBP 1,000,000.\n\n"
        "Charitable legacies totalling GBP 75,000 are deductible from the estate before IHT "
        "calculation. The net chargeable estate is therefore:\n"
        "  GBP 1,762,800 - GBP 75,000 (charitable) - GBP 1,000,000 (NRBs) = GBP 687,800\n\n"
        "IHT at 40%: GBP 275,120\n\n"
        "Note: The estate may qualify for the reduced IHT rate of 36% as the charitable legacies "
        "exceed 10% of the baseline amount. This requires further calculation but could reduce "
        "the IHT liability to approximately GBP 247,608, a saving of GBP 27,512."
    )
    pdf.add_subtitle("5. Contested Issues")
    pdf.add_body(
        "Mr. Daniel Chen has indicated through his solicitors (Henderson & Co, Auckland) that he "
        "intends to challenge the specific devise of 9 Sycamore Lane to Emily under Clause 7 of "
        "the Will. His grounds are:\n"
        "  (a) The property was the family home and should form part of the residuary estate;\n"
        "  (b) Alleged undue influence by Emily over the deceased during his illness; and\n"
        "  (c) Lack of testamentary capacity at the date of execution (15 March 2023), as the "
        "deceased had been diagnosed with early-stage pancreatic cancer in February 2023.\n\n"
        "We have obtained a letter from Dr. Sarah Pemberton (Mr. Chen's GP) dated 12 March 2023 "
        "confirming that she assessed Mr. Chen's capacity using the Banks v Goodfellow criteria "
        "three days before the Will was executed and found him to have full testamentary capacity."
    )

    # --- Page 4 ---
    pdf.add_page()
    pdf.add_subtitle("6. Response to Challenge")
    pdf.add_body(
        "We assess Daniel's challenge as having weak prospects of success for the following reasons:\n\n"
        "6.1 Testamentary Capacity: The GP's capacity assessment is contemporaneous and directly "
        "addresses the Banks v Goodfellow (1870) criteria. A cancer diagnosis does not per se "
        "impair testamentary capacity.\n\n"
        "6.2 Undue Influence: In Hubbard v Scott [2011] EWHC 2750 (Ch), the court held that the "
        "burden of proving undue influence in testamentary cases rests on the challenger, and mere "
        "opportunity (living nearby) is insufficient. Daniel has provided no positive evidence of "
        "coercion or pressure.\n\n"
        "6.3 Knowledge and Approval: The Will was prepared by an independent solicitor (not this "
        "firm) and the attestation clause confirms the Will was read over to the testator.\n\n"
        "Recommendation: Respond robustly to Henderson & Co. applying for a Larke v Nugus statement "
        "from the instructing solicitor. If Daniel persists, apply to the court for a pronouncement "
        "in solemn form under CPR Part 57."
    )
    pdf.add_subtitle("7. Next Steps")
    pdf.add_body(
        "7.1 File IHT400 with HMRC and apply for Grant of Probate.\n"
        "7.2 Obtain formal valuations for the Lake District property and the jade collection.\n"
        "7.3 Write to Henderson & Co. requesting particulars of Daniel's challenge.\n"
        "7.4 Arrange for the estate's liquid assets to be consolidated into the executor's account."
    )

    path = os.path.join(OUTPUT_DIR, "Chen_Estate_Probate.pdf")
    pdf.output(path)
    print(f"Created: {path}")


def doc4_dataflow_ip():
    """Case 4: Intellectual property -- DataFlow Systems v NexGen Analytics."""
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Page 1 ---
    pdf.add_page()
    pdf.add_title("CONFIDENTIAL CLIENT FILE")
    pdf.add_subtitle("DataFlow Systems Ltd v NexGen Analytics Ltd -- IP Dispute")
    pdf.add_body(
        "File Reference: DF/2025/0217\n"
        "Date Opened: 3 February 2025\n"
        "Fee Earner: Mr. Christopher Lane, Partner (IP & Technology)\n"
        "Client: DataFlow Systems Ltd (Company No. 09127384)\n"
        "Opponent: NexGen Analytics Ltd (Company No. 12845691)"
    )
    pdf.add_subtitle("1. Client Background")
    pdf.add_body(
        "DataFlow Systems Ltd is a United Kingdom-based software company founded in 2014 by "
        "Dr. Helen Osei and Mr. Rajesh Kapoor. The company specialises in real-time data pipeline "
        "management software for the financial services sector. It employs 85 staff and has annual "
        "revenue of approximately GBP 12.4 million (FY 2024).\n\n"
        "DataFlow's principal product is 'StreamCore', a proprietary low-latency data ingestion "
        "and transformation platform. StreamCore uses a novel adaptive partitioning algorithm "
        "(the 'Osei-Kapoor Algorithm') which is the subject of UK Patent No. GB2587412B, granted "
        "on 22 September 2021."
    )
    pdf.add_subtitle("2. The Dispute")
    pdf.add_body(
        "NexGen Analytics Ltd was founded in July 2023 by Mr. Marcus Webb and Ms. Anya Petrov. "
        "Mr. Webb was formerly employed by DataFlow as a Senior Software Engineer from March 2019 "
        "to June 2023. During his employment, Mr. Webb had direct access to the StreamCore source "
        "code and was a named contributor to the development of the Osei-Kapoor Algorithm.\n\n"
        "In October 2024, NexGen launched a competing product called 'FlowEngine'. DataFlow's "
        "technical team conducted a comparative analysis in November 2024 and identified significant "
        "similarities between FlowEngine and StreamCore, particularly in the data partitioning "
        "module."
    )

    # --- Page 2 ---
    pdf.add_page()
    pdf.add_subtitle("3. Evidence of Infringement")
    pdf.add_body(
        "3.1 Patent Infringement (UK Patent GB2587412B):\n"
        "An independent expert, Professor Andrew Whittle (Professor of Computer Science, Imperial "
        "College London), was instructed to analyse FlowEngine. Professor Whittle's preliminary "
        "report dated 15 January 2025 concludes that:\n"
        "  - FlowEngine's partitioning algorithm replicates all 7 claims of GB2587412B;\n"
        "  - The implementation uses identical variable naming conventions in 43 instances, "
        "indicating likely direct copying rather than independent development;\n"
        "  - The algorithmic approach to handling edge cases (Claims 4 and 5) is identical, "
        "including an unusual error-handling pattern that has no functional necessity.\n\n"
        "3.2 Trade Secret Misappropriation:\n"
        "Mr. Webb's employment contract (dated 4 March 2019) contained:\n"
        "  - Clause 12.1: A confidentiality obligation covering all proprietary software and "
        "algorithms, surviving termination indefinitely;\n"
        "  - Clause 14.3: A 12-month post-termination non-compete restriction within the "
        "financial data analytics sector;\n"
        "  - Clause 14.5: A 12-month restriction on soliciting DataFlow's clients.\n\n"
        "Mr. Webb resigned on 30 June 2023. NexGen was incorporated 14 days later on 14 July 2023. "
        "FlowEngine entered development in August 2023, within the 12-month non-compete period."
    )

    # --- Page 3 ---
    pdf.add_page()
    pdf.add_subtitle("4. Commercial Impact")
    pdf.add_body(
        "Since FlowEngine's launch in October 2024, DataFlow has experienced:\n"
        "  - Loss of two major clients: Harrington Capital (annual contract value GBP 480,000) "
        "and Westfield Asset Management (annual contract value GBP 310,000), both of whom "
        "migrated to FlowEngine;\n"
        "  - Three prospective client engagements lost during competitive tender processes "
        "(estimated combined annual value: GBP 620,000);\n"
        "  - Downward pricing pressure on existing contracts, estimated at 8-12% reduction.\n\n"
        "DataFlow estimates its total financial loss to date at GBP 1,410,000, comprising "
        "GBP 790,000 in lost contract revenue and GBP 620,000 in lost prospective contracts. "
        "Ongoing annual losses are projected at GBP 950,000 if NexGen continues to operate "
        "FlowEngine."
    )
    pdf.add_subtitle("5. Remedies Sought")
    pdf.add_body(
        "DataFlow instructs this firm to pursue the following remedies:\n\n"
        "5.1 Interim Injunction: An urgent application for an interim injunction to restrain NexGen "
        "from offering, marketing, or licensing FlowEngine pending trial (American Cyanamid "
        "principles).\n\n"
        "5.2 Patent Infringement Claim: Proceedings in the Intellectual Property Enterprise Court "
        "(IPEC) for infringement of GB2587412B, seeking damages or an account of profits.\n\n"
        "5.3 Breach of Confidence / Trade Secrets: Claim under the Trade Secrets (Enforcement, etc.) "
        "Regulations 2018 (implementing the EU Trade Secrets Directive) for misuse of confidential "
        "information.\n\n"
        "5.4 Breach of Restrictive Covenants: Claim against Mr. Webb personally for breach of the "
        "non-compete covenant (Clause 14.3) and confidentiality obligation (Clause 12.1).\n\n"
        "5.5 Delivery Up / Destruction: An order for delivery up and destruction of all copies of "
        "FlowEngine source code derived from DataFlow's proprietary materials."
    )

    # --- Page 4 ---
    pdf.add_page()
    pdf.add_subtitle("6. Risk Assessment and Strategy")
    pdf.add_body(
        "6.1 Patent Claim Strength: Strong (80-85%). Professor Whittle's evidence of identical "
        "variable naming and error-handling patterns is compelling evidence of copying.\n\n"
        "6.2 Trade Secret Claim: Strong (75-80%). The timing of NexGen's incorporation (14 days "
        "after resignation) and the speed of FlowEngine development support an inference of "
        "misuse.\n\n"
        "6.3 Non-Compete Covenant: Moderate (60-70%). The 12-month duration and sector-specific "
        "scope are likely enforceable under Tillman v Egon Zehnder [2019] UKSC 32, but NexGen "
        "was incorporated 14 days after resignation and did not begin trading until August 2023 -- "
        "a point which NexGen may argue makes the operative date later than incorporation.\n\n"
        "6.4 Injunction Prospects: The American Cyanamid test requires a serious question to be "
        "tried (clearly met), inadequacy of damages (arguable -- DataFlow's reputational harm is "
        "difficult to quantify), and balance of convenience. NexGen will argue that an injunction "
        "would destroy its business."
    )
    pdf.add_subtitle("7. Estimated Costs")
    pdf.add_body(
        "IPEC proceedings (capped regime): GBP 50,000 maximum recoverable costs.\n"
        "Interim injunction application: GBP 25,000 to GBP 35,000.\n"
        "Total estimated costs to trial: GBP 120,000 to GBP 150,000.\n\n"
        "DataFlow has confirmed it is prepared to fund litigation and has considered ATE insurance."
    )

    path = os.path.join(OUTPUT_DIR, "DataFlow_v_NexGen_IP_Dispute.pdf")
    pdf.output(path)
    print(f"Created: {path}")


def doc5_patel_tenancy():
    """Case 5: Landlord-tenant -- Patel tenancy disrepair and deposit dispute."""
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Page 1 ---
    pdf.add_page()
    pdf.add_title("CONFIDENTIAL CLIENT FILE")
    pdf.add_subtitle("Patel -- Residential Tenancy Dispute")
    pdf.add_body(
        "File Reference: AP/2025/0341\n"
        "Date Opened: 10 February 2025\n"
        "Fee Earner: Ms. Rachel Nguyen, Solicitor (Housing)\n"
        "Client: Mr. Amit Patel and Mrs. Sunita Patel\n"
        "Landlord: Mr. George Whitfield, trading as Whitfield Property Rentals"
    )
    pdf.add_subtitle("1. Client Details")
    pdf.add_body(
        "Mr. Amit Patel (aged 34) and Mrs. Sunita Patel (aged 31) reside at 42 Lancaster Road, "
        "Flat 3, Leeds, LS1 4HT, with their two children, Priya (aged 7) and Rohan (aged 4). "
        "Mr. Patel is employed as an NHS pharmacist at Leeds General Infirmary with an annual "
        "salary of GBP 43,500. Mrs. Patel works part-time as a teaching assistant earning "
        "GBP 14,200 per annum."
    )
    pdf.add_subtitle("2. Tenancy Details")
    pdf.add_body(
        "The Patels entered into an Assured Shorthold Tenancy (AST) agreement dated 1 August 2022 "
        "for Flat 3, 42 Lancaster Road, Leeds. The initial fixed term was 12 months, after which "
        "the tenancy continued as a statutory periodic tenancy.\n\n"
        "Key terms:\n"
        "  - Monthly rent: GBP 1,150 (increased from GBP 1,050 on 1 August 2023 via s.13 notice)\n"
        "  - Tenancy deposit: GBP 1,575 (stated to be protected with the Deposit Protection Service)\n"
        "  - The property is a two-bedroom flat on the second floor of a converted Victorian house\n"
        "  - The landlord is responsible for structural and exterior repairs, heating, hot water, "
        "and sanitation under s.11 Landlord and Tenant Act 1985"
    )

    # --- Page 2 ---
    pdf.add_page()
    pdf.add_subtitle("3. Disrepair Issues")
    pdf.add_body(
        "The Patels have experienced persistent disrepair issues since approximately January 2024. "
        "The following defects have been reported to the landlord in writing on at least three "
        "occasions (letters dated 15 January 2024, 4 April 2024, and 19 August 2024):\n\n"
        "3.1 Damp and Mould: Extensive black mould growth in the main bedroom and the children's "
        "bedroom caused by penetrating damp from a defective roof above the flat. An environmental "
        "health officer from Leeds City Council inspected on 22 May 2024 and served an Improvement "
        "Notice under s.11 Housing Act 2004, requiring remediation within 28 days. The landlord "
        "has not complied.\n\n"
        "3.2 Heating System: The gas central heating boiler (a Vaillant ecoTEC Plus, installed in "
        "2016) has been intermittently failing since November 2023. It broke down completely on "
        "3 December 2024. The family was without heating for 18 days (3-21 December 2024) during "
        "which external temperatures fell below zero on seven occasions. The landlord arranged a "
        "temporary repair on 21 December 2024, but the boiler continues to malfunction.\n\n"
        "3.3 Hot Water: The hot water supply is linked to the defective boiler and has been "
        "unreliable throughout the same period.\n\n"
        "3.4 Window Defects: The sash windows in the living room and main bedroom are rotten and "
        "do not close properly. This causes significant draughts and heat loss and has resulted "
        "in increased energy costs estimated at GBP 65 per month."
    )

    # --- Page 3 ---
    pdf.add_page()
    pdf.add_subtitle("4. Health Impact")
    pdf.add_body(
        "The disrepair has caused the following health consequences, documented by Dr. Imran Shah "
        "(the family GP) in a medical report dated 6 January 2025:\n\n"
        "4.1 Priya Patel (aged 7): Diagnosed with a worsening of her pre-existing asthma, with "
        "three hospital attendances at Leeds Children's Hospital (14 February 2024, 18 June 2024, "
        "and 29 November 2024). Dr. Shah attributes the exacerbation directly to mould exposure.\n\n"
        "4.2 Mrs. Sunita Patel: Diagnosed with stress and anxiety (prescribed sertraline 50mg "
        "since March 2024), attributed by Dr. Shah to the ongoing housing conditions and the "
        "impact on her children.\n\n"
        "4.3 Mr. Amit Patel: Reports significant sleep disruption and stress affecting his work "
        "performance."
    )
    pdf.add_subtitle("5. Deposit Protection Issue")
    pdf.add_body(
        "A search of all three government-approved tenancy deposit schemes (DPS, MyDeposits, and "
        "TDS) conducted on 5 February 2025 confirmed that the Patels' deposit of GBP 1,575 is "
        "NOT currently protected in any scheme. Under s.213 Housing Act 2004, the landlord was "
        "required to protect the deposit within 30 days of receipt (i.e., by 31 August 2022) and "
        "serve prescribed information.\n\n"
        "Failure to protect the deposit entitles the tenant to compensation of between 1x and 3x "
        "the deposit amount (s.214 Housing Act 2004). The court must order repayment of the deposit "
        "or its transfer to a scheme. This also prevents the landlord from serving a valid Section "
        "21 notice until the deposit is protected or returned."
    )

    # --- Page 4 ---
    pdf.add_page()
    pdf.add_subtitle("6. Quantum of Claim")
    pdf.add_body(
        "6.1 General Damages for Disrepair:\n"
        "Following the guidelines in English Churches Housing Group v Shine [2004], a reasonable "
        "assessment for 12 months of serious disrepair affecting two bedrooms and heating is "
        "25-35% of rent paid:\n"
        "  - Rent paid during disrepair period (Jan 2024 - Feb 2025, 14 months): GBP 16,100\n"
        "  - General damages at 30%: GBP 4,830\n\n"
        "6.2 Special Damages:\n"
        "  - Additional heating costs (portable electric heaters): GBP 910\n"
        "  - Increased energy bills from window defects (14 months x GBP 65): GBP 910\n"
        "  - Cost of mould treatment products: GBP 180\n"
        "  - Medical prescription charges: GBP 120\n"
        "  Total special damages: GBP 2,120\n\n"
        "6.3 Deposit Penalty:\n"
        "  - Return of deposit: GBP 1,575\n"
        "  - Compensation (seeking 2x deposit): GBP 3,150\n\n"
        "Total claim value: GBP 11,675"
    )
    pdf.add_subtitle("7. Legal Basis and Strategy")
    pdf.add_body(
        "Disrepair Claim:\n"
        "  - Landlord and Tenant Act 1985, s.11 (implied repairing obligation)\n"
        "  - Homes (Fitness for Human Habitation) Act 2018, s.9A (fitness for habitation)\n"
        "  - Housing Act 2004, ss.11-12 (Housing Health and Safety Rating System)\n"
        "  - Human Rights Act 1998, Article 8 (right to respect for private and family life)\n\n"
        "Deposit Claim:\n"
        "  - Housing Act 2004, ss.213-215\n\n"
        "Strategy: Issue proceedings in the County Court. The deposit claim is unanswerable. The "
        "disrepair claim is strengthened by the Council's Improvement Notice and the medical "
        "evidence. We recommend issuing a Letter Before Action under the Pre-Action Protocol for "
        "Housing Disrepair Cases, with a 20-day response period, before issuing proceedings.\n\n"
        "Prior to issuing proceedings, we should also consider whether a complaint to the Housing "
        "Ombudsman is appropriate, although this route is typically slower than court action."
    )

    path = os.path.join(OUTPUT_DIR, "Patel_Tenancy_Dispute.pdf")
    pdf.output(path)
    print(f"Created: {path}")


if __name__ == "__main__":
    doc1_thompson_v_meridian()
    doc2_williams_employment()
    doc3_chen_estate()
    doc4_dataflow_ip()
    doc5_patel_tenancy()
    print(f"\nAll 5 test documents generated in: {OUTPUT_DIR}")
