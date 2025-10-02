#include <cmath>
#include "MathUtil.h"

double norm_cdf(const double value) {
    return 0.5 * (1 + (std::erf(value / sqrt(2))));
}

double norm_pdf(const double value) {
    return (1.0 / std::sqrt(2 * M_PI) * std::exp(-0.5 * value * value));
}