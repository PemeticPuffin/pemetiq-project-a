"""Pre-loaded example output for Apple Inc. (AAPL) — shown on first load."""

from src.analysis.per_source import Finding, SourceAnalysis
from src.analysis.synthesis import Contradiction, SynthesisResult
from src.entity_resolver import ResolvedEntity

EXAMPLE_ENTITY = ResolvedEntity(
    cik=320193,
    legal_name="Apple Inc.",
    ticker="AAPL",
)

EXAMPLE_SOURCE_ANALYSES = [
    SourceAnalysis(
        source_name="SEC Filing",
        findings=[
            Finding(
                category="Revenue Concentration",
                text="iPhone remains the dominant revenue driver at ~52% of total net sales, creating meaningful concentration risk if consumer upgrade cycles slow or a major product cycle disappoints.",
                confidence="High",
            ),
            Finding(
                category="Services Growth",
                text="Services segment revenue grew double-digits year-over-year and now represents the highest-margin business within Apple, with management explicitly calling it a strategic priority for operating leverage.",
                confidence="High",
            ),
            Finding(
                category="Competitive Moat",
                text="Apple's integrated hardware-software-services ecosystem creates high switching costs. The filing cites over 2 billion active devices as the installed base underpinning services monetization.",
                confidence="High",
            ),
            Finding(
                category="Regulatory Risk",
                text="The filing dedicates significant risk factor language to antitrust and App Store regulatory pressure across the EU, US, and Asia. Potential forced changes to App Store economics represent a material risk to Services margins.",
                confidence="High",
            ),
            Finding(
                category="China Exposure",
                text="Greater China accounted for approximately 19% of revenue. The filing acknowledges geopolitical risk, trade policy uncertainty, and local competition from Huawei as ongoing risk factors.",
                confidence="High",
            ),
            Finding(
                category="R&D Investment",
                text="R&D spend has increased steadily as a percentage of revenue, consistent with investment in AI/ML capabilities, though the filing does not disclose specific project allocations.",
                confidence="Medium",
            ),
            Finding(
                category="Capital Return",
                text="Apple returned over $100B to shareholders via buybacks and dividends in the most recent fiscal year, reflecting high free cash flow generation and management's view that the stock is attractive at current levels.",
                confidence="High",
            ),
            Finding(
                category="Supply Chain",
                text="The filing cites single-source supplier dependencies for certain components. TSMC is implicitly the primary advanced chip manufacturer, creating concentration risk that management is partially mitigating via geographic diversification of assembly.",
                confidence="Medium",
            ),
        ],
    ),
    SourceAnalysis(
        source_name="Recent News",
        findings=[
            Finding(
                category="AI Product Narrative",
                text="Recent coverage is dominated by Apple Intelligence feature rollout and its reception. Headlines are mixed — enthusiasm for on-device privacy approach but criticism of delayed and limited initial feature set versus competitors.",
                confidence="High",
            ),
            Finding(
                category="China Competition",
                text="Multiple outlets reported Huawei's Mate series recovery gaining share in premium China market, coinciding with a quarter of softer iPhone sales in Greater China. Analyst downgrades cited this specifically.",
                confidence="High",
            ),
            Finding(
                category="Regulatory Action",
                text="EU Digital Markets Act enforcement resulted in Apple opening third-party app distribution in Europe. News coverage suggests developer reaction is cautiously optimistic but user adoption of alternative stores has been minimal so far.",
                confidence="Medium",
            ),
            Finding(
                category="Vision Pro Reception",
                text="Coverage of Vision Pro has shifted from launch excitement to questions about mainstream adoption timeline. Several outlets cited low sales volumes and developer hesitancy to invest in visionOS platform.",
                confidence="Medium",
            ),
            Finding(
                category="Management Tone",
                text="Tim Cook's public statements emphasize AI as the next major computing platform shift, consistent with increased R&D signaling in filings. No leadership transition news.",
                confidence="High",
            ),
        ],
    ),
    SourceAnalysis(
        source_name="Google Trends",
        findings=[
            Finding(
                category="Search Interest Trend",
                text="Apple search interest has been stable to slightly declining over the past 90 days on the 0–100 scale, with no sustained upward momentum — consistent with a mature brand in a maturing upgrade cycle.",
                confidence="Medium",
            ),
            Finding(
                category="iPhone Spike",
                text="A notable spike in search interest coincided with the iPhone 16 launch window, returning to baseline within 3 weeks — typical launch-cycle pattern with no extended consumer excitement tail.",
                confidence="High",
            ),
            Finding(
                category="Rising Queries",
                text="'Apple Intelligence' and 'Apple AI' appear in rising related queries, indicating genuine consumer curiosity about the AI feature set — though curiosity does not yet confirm purchase intent.",
                confidence="Medium",
            ),
            Finding(
                category="Vision Pro Interest",
                text="Search interest for 'Apple Vision Pro' has declined significantly from launch peak and is now at low baseline levels, corroborating news coverage of limited mainstream traction.",
                confidence="High",
            ),
        ],
    ),
]

EXAMPLE_SYNTHESIS = SynthesisResult(
    company_name="Apple Inc.",
    ticker="AAPL",
    executive_summary=(
        "Apple remains a high-quality business with durable competitive advantages — "
        "an 2B+ device installed base, expanding Services margins, and best-in-class capital returns. "
        "However, three converging signals warrant attention: iPhone growth is plateauing in its largest markets, "
        "the AI product narrative is generating curiosity without clear purchase-cycle pull-through, "
        "and regulatory pressure on App Store economics threatens the highest-margin growth engine. "
        "The China exposure remains the most binary near-term risk, with Huawei competition showing "
        "real traction in the premium segment where Apple earns its highest ASPs."
    ),
    reinforcing_signals=[
        "China headwinds confirmed across all three sources: SEC filing flags geopolitical risk, news coverage reports Huawei share gains, and Greater China revenue softness is reflected in analyst commentary.",
        "Services is the strategic priority: SEC filing highlights Services margin expansion, news coverage of App Store regulatory battles confirms its centrality, and management public statements reinforce this narrative.",
        "AI curiosity is real but conversion is unproven: Google Trends rising queries for 'Apple Intelligence' align with news coverage of mixed feature reception — interest exists but no purchase pull-through signal yet.",
        "Vision Pro is underperforming expectations: declining Trends interest, skeptical news coverage, and low developer investment signals all point the same direction.",
    ],
    contradictions=[
        Contradiction(
            claim="Magnitude of China risk impact on near-term revenue",
            source_a="SEC Filing: frames China as a risk factor among many, with balanced language around long-term opportunity.",
            source_b="Recent News: analyst downgrades and specific quarter data suggest China softness is already a current-quarter earnings headwind, not a future risk.",
            significance="If China impact is already flowing through revenue, guidance conservatism may be understated in management commentary.",
        ),
        Contradiction(
            claim="Consumer reception of Apple Intelligence AI features",
            source_a="Recent News: coverage is mixed-to-skeptical, with critics noting delayed rollout and limited capabilities vs. competitors.",
            source_b="Google Trends: rising queries for 'Apple Intelligence' suggest genuine consumer interest and awareness.",
            significance="Awareness and interest do not equal satisfaction — the divergence suggests a potential gap between consumer curiosity and actual product experience that could affect upgrade intent.",
        ),
    ],
    notable_absences=[
        "No clear signal on when Vision Pro reaches a price point or use case that drives mainstream adoption — neither filings nor news nor search trends suggest this is imminent.",
        "India as an explicit growth offset to China weakness is mentioned in news but largely absent from Trends data, suggesting consumer mindshare in India is still early-stage.",
        "No analyst or news signal on succession planning depth, which is notable for a company this size given Tim Cook's tenure.",
    ],
    watch_signals=[
        "App Store regulatory outcomes in the EU and US: any forced change to the 30% commission model would have outsized impact on Services margin — the single most important watch item.",
        "iPhone 17 cycle search interest in the 6–8 weeks before launch: will it show the same muted post-launch tail as iPhone 16, or recover upgrade cycle momentum?",
        "Huawei Mate series market share data for Q1 2026 in China: continued gains would pressure Apple's Greater China revenue more than current consensus expects.",
        "Apple Intelligence adoption metrics: if Apple discloses or leaks feature engagement data, it will be the first real signal of whether AI is a meaningful upgrade cycle catalyst.",
    ],
)
