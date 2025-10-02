#include "Option.h"
#include "MathUtil.h"
#include <cmath>
#include <iostream>

Option::Option(double r, double s, double k, double t, double sigma, OptionType optType) {
    this->riskFreeIntrestRate = r;
    this->underlyingPrice = s;
    this->strikePrice = k;
    this->timeToExpiryOverYear = t;
    this->volatility = sigma;
    this->optionType = optType;
}

double Option::price() const {
    const double d1 = this->calculateD1();
    const double d2 = this->calculateD2();
    double finalPrice = 0.0;

    if (optionType == OptionType::Call) {
        finalPrice = (underlyingPrice * norm_cdf(d1)) -
                     (strikePrice * std::exp(-riskFreeIntrestRate * timeToExpiryOverYear) * norm_cdf(d2));
    } else if (optionType == OptionType::Put) {
        finalPrice = (strikePrice * std::exp(-riskFreeIntrestRate * timeToExpiryOverYear) * norm_cdf(-d2)) -
                     (underlyingPrice * norm_cdf(-d1));
    }
    return finalPrice;
}

double Option::delta() const {
    const double d1 = this->calculateD1();
    if (optionType == OptionType::Call) {
        return norm_cdf(d1);
    } else {
        return norm_cdf(d1) - 1.0;
    }
}

double Option::gamma() const {
    const double numerator = norm_pdf(this->calculateD1());
    const double denominator = underlyingPrice * volatility * std::sqrt(timeToExpiryOverYear);
    return numerator / denominator;
}

double Option::vega() const {
    return underlyingPrice * norm_pdf(this->calculateD1()) * std::sqrt(timeToExpiryOverYear);
}

double Option::theta() const {
    const double d1 = this->calculateD1();
    const double d2 = this->calculateD2();
    const double term1 = -(underlyingPrice * norm_pdf(d1) * volatility) / (2 * std::sqrt(timeToExpiryOverYear));

    if (optionType == OptionType::Call) {
        const double term2 = riskFreeIntrestRate * strikePrice * std::exp(-riskFreeIntrestRate * timeToExpiryOverYear) * norm_cdf(d2);
        return term1 - term2;
    } else {
        const double term2 = riskFreeIntrestRate * strikePrice * std::exp(-riskFreeIntrestRate * timeToExpiryOverYear) * norm_cdf(-d2);
        return term1 + term2;
    }
}

double Option::rho() const {
    const double d2 = this->calculateD2();
    if (optionType == OptionType::Call) {
        return strikePrice * timeToExpiryOverYear * std::exp(-riskFreeIntrestRate * timeToExpiryOverYear) * norm_cdf(d2);
    } else {
        return -strikePrice * timeToExpiryOverYear * std::exp(-riskFreeIntrestRate * timeToExpiryOverYear) * norm_cdf(-d2);
    }
}

double Option::impliedVolatility(double marketPrice) const {
    double tolerance = 1e-5;
    int maxIterations = 100;
    double vol = this->volatility;

    for (int i = 0; i < maxIterations; ++i) {

        std::cout << "--- Iteration " << i << " ---" << std::endl;

        Option tempOption(riskFreeIntrestRate, underlyingPrice, strikePrice,
                          timeToExpiryOverYear, vol, optionType);

        double priceDiff = tempOption.price() - marketPrice;
        double vega = tempOption.vega();

        std::cout << "Price Difference: " << priceDiff << std::endl;
        std::cout << "Vega: " << vega << std::endl;

        if (std::abs(priceDiff) < tolerance) {
            return vol;
        }

        if (std::abs(vega) < 1e-6) {
            break;
        }

        vol -= priceDiff / vega;
    }

    return vol;
}

double Option::calculateD1() const {
    const double term1 = std::log(underlyingPrice / strikePrice);
    const double term2 = (riskFreeIntrestRate + (volatility * volatility) / 2) * timeToExpiryOverYear;
    const double denominator = volatility * std::sqrt(timeToExpiryOverYear);
    return (term1 + term2) / denominator;
}

double Option::calculateD2() const {
    return calculateD1() - (volatility * std::sqrt(timeToExpiryOverYear));
}
