package validators

import (
	"fmt"
	"log"
	"strings"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// RVSValidator runs comprehensive validation over RVS inputs before the
// engine is invoked.
type RVSValidator struct {
	logger *log.Logger
}

func NewRVSValidator(logger *log.Logger) *RVSValidator {
	return &RVSValidator{logger: logger}
}

// ValidateRVSInput enforces required fields, ranges, and cross-field rules.
func (v *RVSValidator) ValidateRVSInput(input models.RVSv4Input) error {
	var errs []string

	if input.TotalAssets <= 0 {
		errs = append(errs, "totalAssets must be greater than zero")
	}
	if input.Revenue <= 0 {
		errs = append(errs, "revenue must be greater than zero")
	}
	if input.TotalDebt < 0 {
		errs = append(errs, "totalDebt cannot be negative")
	}
	if input.CollateralValue < 0 {
		errs = append(errs, "collateralValue cannot be negative")
	}
	if input.TotalLiabilities < 0 {
		errs = append(errs, "totalLiabilities cannot be negative")
	}

	if input.TotalAssets > 0 {
		leverage := input.TotalLiabilities / input.TotalAssets
		if leverage > 5.0 {
			errs = append(errs, fmt.Sprintf("leverage ratio (%.2f) exceeds maximum threshold of 5.0", leverage))
		}
	}

	if input.Revenue > 0 {
		margin := (input.EBITDA / input.Revenue) * 100
		if margin < -100 {
			errs = append(errs, fmt.Sprintf("EBITDA margin (%.1f%%) is unreasonably low", margin))
		}
		if margin > 100 {
			errs = append(errs, fmt.Sprintf("EBITDA margin (%.1f%%) exceeds 100%% - verify calculation", margin))
		}
	}

	if input.RPTRevenuePercent < 0 || input.RPTRevenuePercent > 100 {
		errs = append(errs, "rptRevenuePercent must be between 0 and 100")
	}
	if input.RPTCostPercent < 0 || input.RPTCostPercent > 100 {
		errs = append(errs, "rptCostPercent must be between 0 and 100")
	}
	if input.InformationAsymmetryPercent < 0 || input.InformationAsymmetryPercent > 20 {
		errs = append(errs, "informationAsymmetryPercent must be between 0 and 20")
	}
	if input.GovernanceScore < 0 || input.GovernanceScore > 100 {
		errs = append(errs, "governanceScore must be between 0 and 100")
	}
	if input.ConcentrationScore < 0 || input.ConcentrationScore > 100 {
		errs = append(errs, "concentrationScore must be between 0 and 100")
	}
	if input.AppraisalFactor < 0.1 || input.AppraisalFactor > 3.0 {
		errs = append(errs, "appraisalFactor must be between 0.1 and 3.0")
	}
	if input.RevenueUnderreportingFactor < 0.5 || input.RevenueUnderreportingFactor > 2.0 {
		errs = append(errs, "revenueUnderreportingFactor must be between 0.5 and 2.0")
	}

	if input.CollateralValue > input.TotalAssets*1.5 {
		errs = append(errs, "collateralValue exceeds 150% of totalAssets - verify appraisal")
	}

	if input.TotalDebt > 0 {
		coverage := input.CollateralValue / input.TotalDebt
		if coverage < 0.3 {
			v.logger.Printf("Warning: Collateral coverage ratio is very low (%.2f)", coverage)
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("validation failed: %s", strings.Join(errs, "; "))
	}
	return nil
}
