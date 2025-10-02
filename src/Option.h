#ifndef OPTION_H
#define OPTION_H

enum class OptionType { Call, Put };

class Option {
public:
    Option(double r, double s, double k, double t, double sigma, OptionType optType);

    [[nodiscard]] double price() const;
    [[nodiscard]] double delta() const;
    [[nodiscard]] double gamma() const;
    [[nodiscard]] double vega() const;
    [[nodiscard]] double theta() const;
    [[nodiscard]] double rho() const;
    [[nodiscard]] double impliedVolatility(double marketPrice) const;

private:
    double riskFreeIntrestRate;
    double underlyingPrice;
    double strikePrice;
    double timeToExpiryOverYear;
    double volatility;
    OptionType optionType;

    [[nodiscard]] double calculateD1() const;
    [[nodiscard]] double calculateD2() const;
};

#endif