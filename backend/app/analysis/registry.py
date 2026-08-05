from app.models import AnalysisMethod

P0_METHODS = frozenset(
    {
        AnalysisMethod.DESCRIPTIVE_STATISTICS,
        AnalysisMethod.PEARSON_CORRELATION,
        AnalysisMethod.SPEARMAN_CORRELATION,
        AnalysisMethod.INDEPENDENT_TWO_GROUP,
        AnalysisMethod.PAIRED_TWO_GROUP,
        AnalysisMethod.SIMPLE_LINEAR_REGRESSION,
    }
)


def require_supported(method: AnalysisMethod) -> None:
    if method not in P0_METHODS:
        raise ValueError("Analysis method is not implemented in M5")
