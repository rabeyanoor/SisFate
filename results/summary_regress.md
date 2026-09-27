# PERSIST results summary (cc_mode=regress)


## within

|                                                     |   auroc |   auroc_sd |    lo |    hi |   auprc |   lift |   wc_auroc |   prevalence |   n_seeds |   auroc_shuf |   auroc_shuf_sd |
|:----------------------------------------------------|--------:|-----------:|------:|------:|--------:|-------:|-----------:|-------------:|----------:|-------------:|----------------:|
| ('cov_logreg', 'Carboplatin', 'Carboplatin')        |   0.613 |        nan | 0.592 | 0.632 |   0.107 |  1.307 |      0.602 |        0.082 |         1 |        0.478 |           0.018 |
| ('cov_logreg', 'Control', 'Control')                |   0.589 |        nan | 0.566 | 0.611 |   0.172 |  1.165 |      0.589 |        0.148 |         1 |        0.484 |           0.018 |
| ('cov_logreg', 'NK', 'NK')                          |   0.651 |        nan | 0.631 | 0.668 |   0.123 |  1.469 |      0.646 |        0.083 |         1 |        0.498 |           0.018 |
| ('cov_logreg', 'Olaparib', 'Olaparib')              |   0.596 |        nan | 0.579 | 0.612 |   0.113 |  1.177 |      0.576 |        0.096 |         1 |        0.509 |           0.026 |
| ('hvg_logreg', 'Carboplatin', 'Carboplatin')        |   0.643 |        nan | 0.623 | 0.663 |   0.127 |  1.543 |      0.622 |        0.082 |         1 |        0.518 |           0.012 |
| ('hvg_logreg', 'Control', 'Control')                |   0.626 |        nan | 0.601 | 0.648 |   0.201 |  1.364 |      0.61  |        0.148 |         1 |        0.527 |           0.013 |
| ('hvg_logreg', 'NK', 'NK')                          |   0.626 |        nan | 0.609 | 0.645 |   0.128 |  1.534 |      0.605 |        0.083 |         1 |        0.507 |           0.006 |
| ('hvg_logreg', 'Olaparib', 'Olaparib')              |   0.654 |        nan | 0.636 | 0.672 |   0.152 |  1.577 |      0.627 |        0.096 |         1 |        0.512 |           0.015 |
| ('pca_logreg', 'Carboplatin', 'Carboplatin')        |   0.748 |        nan | 0.732 | 0.765 |   0.197 |  2.401 |      0.715 |        0.082 |         1 |        0.507 |           0.016 |
| ('pca_logreg', 'Control', 'Control')                |   0.707 |        nan | 0.683 | 0.728 |   0.249 |  1.686 |      0.69  |        0.148 |         1 |        0.526 |           0.03  |
| ('pca_logreg', 'NK', 'NK')                          |   0.725 |        nan | 0.709 | 0.74  |   0.169 |  2.023 |      0.707 |        0.083 |         1 |        0.488 |           0.024 |
| ('pca_logreg', 'Olaparib', 'Olaparib')              |   0.743 |        nan | 0.727 | 0.761 |   0.221 |  2.293 |      0.704 |        0.096 |         1 |        0.51  |           0.013 |
| ('pca_logreg_pooled', 'Carboplatin', 'Carboplatin') |   0.748 |        nan | 0.731 | 0.764 |   0.195 |  2.368 |      0.716 |        0.082 |         1 |        0.504 |           0.007 |
| ('pca_logreg_pooled', 'Control', 'Control')         |   0.711 |        nan | 0.688 | 0.733 |   0.262 |  1.774 |      0.707 |        0.148 |         1 |        0.479 |           0.01  |
| ('pca_logreg_pooled', 'NK', 'NK')                   |   0.726 |        nan | 0.711 | 0.741 |   0.173 |  2.07  |      0.712 |        0.083 |         1 |        0.566 |           0.009 |
| ('pca_logreg_pooled', 'Olaparib', 'Olaparib')       |   0.746 |        nan | 0.729 | 0.763 |   0.223 |  2.317 |      0.712 |        0.096 |         1 |        0.514 |           0.006 |
| ('pca_logreg_tuned', 'Carboplatin', 'Carboplatin')  |   0.748 |        nan | 0.73  | 0.764 |   0.195 |  2.37  |      0.714 |        0.082 |         1 |        0.512 |         nan     |
| ('pca_logreg_tuned', 'Control', 'Control')          |   0.707 |        nan | 0.683 | 0.728 |   0.249 |  1.687 |      0.69  |        0.148 |         1 |        0.53  |         nan     |
| ('pca_logreg_tuned', 'NK', 'NK')                    |   0.725 |        nan | 0.708 | 0.74  |   0.168 |  2.018 |      0.707 |        0.083 |         1 |        0.53  |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'Olaparib')        |   0.743 |        nan | 0.727 | 0.761 |   0.219 |  2.277 |      0.704 |        0.096 |         1 |        0.494 |         nan     |
| ('pca_smooth_logreg', 'Carboplatin', 'Carboplatin') |   0.75  |        nan | 0.732 | 0.766 |   0.2   |  2.434 |      0.715 |        0.082 |         1 |        0.503 |           0.015 |
| ('pca_smooth_logreg', 'Control', 'Control')         |   0.703 |        nan | 0.679 | 0.725 |   0.248 |  1.678 |      0.68  |        0.148 |         1 |        0.509 |           0.009 |
| ('pca_smooth_logreg', 'NK', 'NK')                   |   0.722 |        nan | 0.706 | 0.738 |   0.169 |  2.029 |      0.703 |        0.083 |         1 |        0.496 |           0.025 |
| ('pca_smooth_logreg', 'Olaparib', 'Olaparib')       |   0.747 |        nan | 0.731 | 0.765 |   0.223 |  2.318 |      0.707 |        0.096 |         1 |        0.508 |           0.017 |


## rep_holdout

|                                                         |   auroc |   auroc_sd |    lo |    hi |   auprc |   lift |   wc_auroc |   prevalence |   n_seeds |   auroc_shuf |   auroc_shuf_sd |
|:--------------------------------------------------------|--------:|-----------:|------:|------:|--------:|-------:|-----------:|-------------:|----------:|-------------:|----------------:|
| ('cov_logreg', 'Carboplatin_1', 'Carboplatin_2')        |   0.626 |        nan | 0.599 | 0.655 |   0.119 |  1.383 |      0.621 |        0.086 |         1 |        0.49  |           0.078 |
| ('cov_logreg', 'Carboplatin_2', 'Carboplatin_1')        |   0.613 |        nan | 0.586 | 0.64  |   0.1   |  1.278 |      0.594 |        0.078 |         1 |        0.502 |           0.067 |
| ('cov_logreg', 'Control_1', 'Control_2')                |   0.589 |        nan | 0.548 | 0.628 |   0.172 |  1.154 |      0.588 |        0.149 |         1 |        0.521 |           0.035 |
| ('cov_logreg', 'Control_2', 'Control_1')                |   0.595 |        nan | 0.564 | 0.626 |   0.174 |  1.183 |      0.597 |        0.147 |         1 |        0.496 |           0.048 |
| ('cov_logreg', 'NK_1', 'NK_2')                          |   0.664 |        nan | 0.645 | 0.687 |   0.124 |  1.508 |      0.66  |        0.082 |         1 |        0.43  |           0.031 |
| ('cov_logreg', 'NK_2', 'NK_1')                          |   0.627 |        nan | 0.594 | 0.653 |   0.119 |  1.4   |      0.616 |        0.085 |         1 |        0.513 |           0.066 |
| ('cov_logreg', 'Olaparib_1', 'Olaparib_2')              |   0.588 |        nan | 0.561 | 0.613 |   0.095 |  1.181 |      0.555 |        0.08  |         1 |        0.469 |           0.048 |
| ('cov_logreg', 'Olaparib_2', 'Olaparib_1')              |   0.6   |        nan | 0.575 | 0.625 |   0.132 |  1.18  |      0.587 |        0.112 |         1 |        0.487 |           0.083 |
| ('hvg_logreg', 'Carboplatin_1', 'Carboplatin_2')        |   0.648 |        nan | 0.622 | 0.674 |   0.137 |  1.586 |      0.618 |        0.086 |         1 |        0.514 |           0.019 |
| ('hvg_logreg', 'Carboplatin_2', 'Carboplatin_1')        |   0.636 |        nan | 0.606 | 0.665 |   0.129 |  1.651 |      0.605 |        0.078 |         1 |        0.521 |           0.016 |
| ('hvg_logreg', 'Control_1', 'Control_2')                |   0.659 |        nan | 0.629 | 0.689 |   0.21  |  1.41  |      0.645 |        0.149 |         1 |        0.518 |           0.028 |
| ('hvg_logreg', 'Control_2', 'Control_1')                |   0.657 |        nan | 0.626 | 0.688 |   0.227 |  1.546 |      0.644 |        0.147 |         1 |        0.516 |           0.012 |
| ('hvg_logreg', 'NK_1', 'NK_2')                          |   0.611 |        nan | 0.584 | 0.633 |   0.118 |  1.427 |      0.589 |        0.082 |         1 |        0.503 |           0.02  |
| ('hvg_logreg', 'NK_2', 'NK_1')                          |   0.613 |        nan | 0.58  | 0.644 |   0.118 |  1.379 |      0.595 |        0.085 |         1 |        0.497 |           0.013 |
| ('hvg_logreg', 'Olaparib_1', 'Olaparib_2')              |   0.645 |        nan | 0.612 | 0.673 |   0.124 |  1.544 |      0.605 |        0.08  |         1 |        0.519 |           0.027 |
| ('hvg_logreg', 'Olaparib_2', 'Olaparib_1')              |   0.641 |        nan | 0.617 | 0.663 |   0.168 |  1.503 |      0.615 |        0.112 |         1 |        0.517 |           0.012 |
| ('pca_logreg', 'Carboplatin_1', 'Carboplatin_2')        |   0.741 |        nan | 0.715 | 0.765 |   0.199 |  2.303 |      0.709 |        0.086 |         1 |        0.442 |           0.026 |
| ('pca_logreg', 'Carboplatin_2', 'Carboplatin_1')        |   0.735 |        nan | 0.707 | 0.76  |   0.183 |  2.348 |      0.7   |        0.078 |         1 |        0.526 |           0.051 |
| ('pca_logreg', 'Control_1', 'Control_2')                |   0.702 |        nan | 0.673 | 0.735 |   0.244 |  1.634 |      0.687 |        0.149 |         1 |        0.492 |           0.032 |
| ('pca_logreg', 'Control_2', 'Control_1')                |   0.703 |        nan | 0.67  | 0.736 |   0.255 |  1.736 |      0.689 |        0.147 |         1 |        0.522 |           0.037 |
| ('pca_logreg', 'NK_1', 'NK_2')                          |   0.712 |        nan | 0.69  | 0.735 |   0.16  |  1.938 |      0.698 |        0.082 |         1 |        0.482 |           0.031 |
| ('pca_logreg', 'NK_2', 'NK_1')                          |   0.699 |        nan | 0.672 | 0.727 |   0.161 |  1.886 |      0.681 |        0.085 |         1 |        0.514 |           0.029 |
| ('pca_logreg', 'Olaparib_1', 'Olaparib_2')              |   0.751 |        nan | 0.724 | 0.775 |   0.202 |  2.522 |      0.698 |        0.08  |         1 |        0.519 |           0.029 |
| ('pca_logreg', 'Olaparib_2', 'Olaparib_1')              |   0.737 |        nan | 0.714 | 0.759 |   0.242 |  2.158 |      0.71  |        0.112 |         1 |        0.534 |           0.05  |
| ('pca_logreg_pooled', 'Carboplatin_1', 'Carboplatin_2') |   0.739 |        nan | 0.714 | 0.763 |   0.192 |  2.224 |      0.708 |        0.086 |         1 |        0.514 |           0.011 |
| ('pca_logreg_pooled', 'Carboplatin_2', 'Carboplatin_1') |   0.754 |        nan | 0.726 | 0.778 |   0.197 |  2.526 |      0.725 |        0.078 |         1 |        0.488 |           0.012 |
| ('pca_logreg_pooled', 'Control_1', 'Control_2')         |   0.713 |        nan | 0.683 | 0.739 |   0.261 |  1.747 |      0.704 |        0.149 |         1 |        0.484 |           0.018 |
| ('pca_logreg_pooled', 'Control_2', 'Control_1')         |   0.703 |        nan | 0.674 | 0.731 |   0.269 |  1.834 |      0.706 |        0.147 |         1 |        0.473 |           0.008 |
| ('pca_logreg_pooled', 'NK_1', 'NK_2')                   |   0.727 |        nan | 0.707 | 0.751 |   0.172 |  2.088 |      0.72  |        0.082 |         1 |        0.576 |           0.019 |
| ('pca_logreg_pooled', 'NK_2', 'NK_1')                   |   0.715 |        nan | 0.688 | 0.742 |   0.174 |  2.039 |      0.694 |        0.085 |         1 |        0.564 |           0.014 |
| ('pca_logreg_pooled', 'Olaparib_1', 'Olaparib_2')       |   0.745 |        nan | 0.717 | 0.771 |   0.194 |  2.421 |      0.701 |        0.08  |         1 |        0.508 |           0.039 |
| ('pca_logreg_pooled', 'Olaparib_2', 'Olaparib_1')       |   0.746 |        nan | 0.723 | 0.767 |   0.256 |  2.285 |      0.718 |        0.112 |         1 |        0.505 |           0.014 |
| ('pca_logreg_tuned', 'Carboplatin_1', 'Carboplatin_2')  |   0.742 |        nan | 0.717 | 0.766 |   0.2   |  2.316 |      0.711 |        0.086 |         1 |        0.539 |         nan     |
| ('pca_logreg_tuned', 'Carboplatin_2', 'Carboplatin_1')  |   0.732 |        nan | 0.704 | 0.758 |   0.177 |  2.268 |      0.696 |        0.078 |         1 |        0.56  |         nan     |
| ('pca_logreg_tuned', 'Control_1', 'Control_2')          |   0.701 |        nan | 0.672 | 0.735 |   0.244 |  1.635 |      0.686 |        0.149 |         1 |        0.504 |         nan     |
| ('pca_logreg_tuned', 'Control_2', 'Control_1')          |   0.684 |        nan | 0.65  | 0.718 |   0.252 |  1.716 |      0.674 |        0.147 |         1 |        0.545 |         nan     |
| ('pca_logreg_tuned', 'NK_1', 'NK_2')                    |   0.712 |        nan | 0.69  | 0.736 |   0.159 |  1.932 |      0.698 |        0.082 |         1 |        0.497 |         nan     |
| ('pca_logreg_tuned', 'NK_2', 'NK_1')                    |   0.698 |        nan | 0.671 | 0.725 |   0.161 |  1.885 |      0.679 |        0.085 |         1 |        0.505 |         nan     |
| ('pca_logreg_tuned', 'Olaparib_1', 'Olaparib_2')        |   0.75  |        nan | 0.723 | 0.774 |   0.201 |  2.504 |      0.698 |        0.08  |         1 |        0.4   |         nan     |
| ('pca_logreg_tuned', 'Olaparib_2', 'Olaparib_1')        |   0.735 |        nan | 0.711 | 0.757 |   0.242 |  2.162 |      0.709 |        0.112 |         1 |        0.511 |         nan     |
| ('pca_smooth_logreg', 'Carboplatin_1', 'Carboplatin_2') |   0.741 |        nan | 0.716 | 0.765 |   0.2   |  2.319 |      0.707 |        0.086 |         1 |        0.513 |           0.035 |
| ('pca_smooth_logreg', 'Carboplatin_2', 'Carboplatin_1') |   0.734 |        nan | 0.705 | 0.761 |   0.179 |  2.295 |      0.701 |        0.078 |         1 |        0.52  |           0.033 |
| ('pca_smooth_logreg', 'Control_1', 'Control_2')         |   0.698 |        nan | 0.671 | 0.73  |   0.242 |  1.621 |      0.68  |        0.149 |         1 |        0.516 |           0.032 |
| ('pca_smooth_logreg', 'Control_2', 'Control_1')         |   0.707 |        nan | 0.676 | 0.739 |   0.263 |  1.79  |      0.694 |        0.147 |         1 |        0.521 |           0.027 |
| ('pca_smooth_logreg', 'NK_1', 'NK_2')                   |   0.713 |        nan | 0.691 | 0.735 |   0.163 |  1.977 |      0.7   |        0.082 |         1 |        0.526 |           0.046 |
| ('pca_smooth_logreg', 'NK_2', 'NK_1')                   |   0.691 |        nan | 0.664 | 0.72  |   0.16  |  1.881 |      0.671 |        0.085 |         1 |        0.519 |           0.017 |
| ('pca_smooth_logreg', 'Olaparib_1', 'Olaparib_2')       |   0.757 |        nan | 0.731 | 0.782 |   0.208 |  2.588 |      0.708 |        0.08  |         1 |        0.475 |           0.062 |
| ('pca_smooth_logreg', 'Olaparib_2', 'Olaparib_1')       |   0.741 |        nan | 0.718 | 0.762 |   0.25  |  2.23  |      0.71  |        0.112 |         1 |        0.526 |           0.066 |


## cross_arm

|                                                  |   auroc |   auroc_sd |    lo |    hi |   auprc |   lift |   wc_auroc |   prevalence |   n_seeds |   auroc_shuf |   auroc_shuf_sd |
|:-------------------------------------------------|--------:|-----------:|------:|------:|--------:|-------:|-----------:|-------------:|----------:|-------------:|----------------:|
| ('cov_logreg', 'Carboplatin', 'Control')         |   0.588 |        nan | 0.565 | 0.611 |   0.173 |  1.169 |      0.593 |        0.148 |         1 |        0.498 |           0.039 |
| ('cov_logreg', 'Carboplatin', 'NK')              |   0.654 |        nan | 0.635 | 0.671 |   0.123 |  1.473 |      0.65  |        0.083 |         1 |        0.55  |           0.081 |
| ('cov_logreg', 'Carboplatin', 'Olaparib')        |   0.602 |        nan | 0.585 | 0.62  |   0.117 |  1.214 |      0.585 |        0.096 |         1 |        0.479 |           0.049 |
| ('cov_logreg', 'Control', 'Carboplatin')         |   0.604 |        nan | 0.583 | 0.625 |   0.104 |  1.266 |      0.596 |        0.082 |         1 |        0.476 |           0.036 |
| ('cov_logreg', 'Control', 'NK')                  |   0.633 |        nan | 0.615 | 0.651 |   0.116 |  1.389 |      0.628 |        0.083 |         1 |        0.496 |           0.078 |
| ('cov_logreg', 'Control', 'Olaparib')            |   0.594 |        nan | 0.577 | 0.612 |   0.114 |  1.18  |      0.581 |        0.096 |         1 |        0.492 |           0.069 |
| ('cov_logreg', 'NK', 'Carboplatin')              |   0.611 |        nan | 0.59  | 0.63  |   0.107 |  1.303 |      0.6   |        0.082 |         1 |        0.467 |           0.049 |
| ('cov_logreg', 'NK', 'Control')                  |   0.583 |        nan | 0.561 | 0.606 |   0.17  |  1.149 |      0.587 |        0.148 |         1 |        0.473 |           0.018 |
| ('cov_logreg', 'NK', 'Olaparib')                 |   0.603 |        nan | 0.585 | 0.62  |   0.117 |  1.212 |      0.583 |        0.096 |         1 |        0.499 |           0.019 |
| ('cov_logreg', 'Olaparib', 'Carboplatin')        |   0.599 |        nan | 0.578 | 0.62  |   0.104 |  1.267 |      0.588 |        0.082 |         1 |        0.489 |           0.041 |
| ('cov_logreg', 'Olaparib', 'Control')            |   0.578 |        nan | 0.556 | 0.601 |   0.167 |  1.133 |      0.583 |        0.148 |         1 |        0.552 |           0.045 |
| ('cov_logreg', 'Olaparib', 'NK')                 |   0.646 |        nan | 0.629 | 0.664 |   0.121 |  1.454 |      0.641 |        0.083 |         1 |        0.549 |           0.082 |
| ('hvg_logreg', 'Carboplatin', 'Control')         |   0.637 |        nan | 0.616 | 0.66  |   0.215 |  1.453 |      0.621 |        0.148 |         1 |        0.52  |           0.011 |
| ('hvg_logreg', 'Carboplatin', 'NK')              |   0.653 |        nan | 0.634 | 0.672 |   0.139 |  1.664 |      0.638 |        0.083 |         1 |        0.51  |           0.01  |
| ('hvg_logreg', 'Carboplatin', 'Olaparib')        |   0.662 |        nan | 0.643 | 0.678 |   0.158 |  1.643 |      0.638 |        0.096 |         1 |        0.524 |           0.009 |
| ('hvg_logreg', 'Control', 'Carboplatin')         |   0.641 |        nan | 0.622 | 0.66  |   0.126 |  1.535 |      0.623 |        0.082 |         1 |        0.509 |           0.011 |
| ('hvg_logreg', 'Control', 'NK')                  |   0.616 |        nan | 0.598 | 0.636 |   0.119 |  1.431 |      0.607 |        0.083 |         1 |        0.509 |           0.01  |
| ('hvg_logreg', 'Control', 'Olaparib')            |   0.643 |        nan | 0.625 | 0.66  |   0.145 |  1.512 |      0.62  |        0.096 |         1 |        0.517 |           0.007 |
| ('hvg_logreg', 'NK', 'Carboplatin')              |   0.658 |        nan | 0.639 | 0.678 |   0.137 |  1.661 |      0.644 |        0.082 |         1 |        0.53  |           0.009 |
| ('hvg_logreg', 'NK', 'Control')                  |   0.629 |        nan | 0.606 | 0.649 |   0.21  |  1.419 |      0.62  |        0.148 |         1 |        0.512 |           0.016 |
| ('hvg_logreg', 'NK', 'Olaparib')                 |   0.634 |        nan | 0.616 | 0.651 |   0.139 |  1.445 |      0.619 |        0.096 |         1 |        0.516 |           0.008 |
| ('hvg_logreg', 'Olaparib', 'Carboplatin')        |   0.685 |        nan | 0.666 | 0.705 |   0.152 |  1.848 |      0.658 |        0.082 |         1 |        0.512 |           0.01  |
| ('hvg_logreg', 'Olaparib', 'Control')            |   0.64  |        nan | 0.617 | 0.664 |   0.211 |  1.426 |      0.624 |        0.148 |         1 |        0.512 |           0.012 |
| ('hvg_logreg', 'Olaparib', 'NK')                 |   0.647 |        nan | 0.628 | 0.664 |   0.144 |  1.725 |      0.632 |        0.083 |         1 |        0.503 |           0.005 |
| ('pca_logreg', 'Carboplatin', 'Control')         |   0.698 |        nan | 0.676 | 0.721 |   0.256 |  1.733 |      0.697 |        0.148 |         1 |        0.497 |           0.025 |
| ('pca_logreg', 'Carboplatin', 'NK')              |   0.712 |        nan | 0.696 | 0.728 |   0.166 |  1.993 |      0.704 |        0.083 |         1 |        0.522 |           0.056 |
| ('pca_logreg', 'Carboplatin', 'Olaparib')        |   0.731 |        nan | 0.713 | 0.749 |   0.217 |  2.253 |      0.698 |        0.096 |         1 |        0.492 |           0.035 |
| ('pca_logreg', 'Control', 'Carboplatin')         |   0.725 |        nan | 0.709 | 0.742 |   0.171 |  2.083 |      0.704 |        0.082 |         1 |        0.552 |           0.023 |
| ('pca_logreg', 'Control', 'NK')                  |   0.7   |        nan | 0.682 | 0.716 |   0.15  |  1.796 |      0.69  |        0.083 |         1 |        0.5   |           0.037 |
| ('pca_logreg', 'Control', 'Olaparib')            |   0.711 |        nan | 0.695 | 0.728 |   0.184 |  1.915 |      0.687 |        0.096 |         1 |        0.503 |           0.023 |
| ('pca_logreg', 'NK', 'Carboplatin')              |   0.73  |        nan | 0.711 | 0.748 |   0.18  |  2.187 |      0.702 |        0.082 |         1 |        0.493 |           0.026 |
| ('pca_logreg', 'NK', 'Control')                  |   0.695 |        nan | 0.673 | 0.719 |   0.245 |  1.658 |      0.695 |        0.148 |         1 |        0.527 |           0.025 |
| ('pca_logreg', 'NK', 'Olaparib')                 |   0.732 |        nan | 0.715 | 0.751 |   0.216 |  2.247 |      0.705 |        0.096 |         1 |        0.519 |           0.043 |
| ('pca_logreg', 'Olaparib', 'Carboplatin')        |   0.737 |        nan | 0.718 | 0.754 |   0.185 |  2.253 |      0.705 |        0.082 |         1 |        0.459 |           0.043 |
| ('pca_logreg', 'Olaparib', 'Control')            |   0.693 |        nan | 0.669 | 0.716 |   0.262 |  1.773 |      0.697 |        0.148 |         1 |        0.527 |           0.045 |
| ('pca_logreg', 'Olaparib', 'NK')                 |   0.712 |        nan | 0.696 | 0.729 |   0.169 |  2.02  |      0.701 |        0.083 |         1 |        0.506 |           0.055 |
| ('pca_logreg_pooled', 'Carboplatin', 'Control')  |   0.704 |        nan | 0.682 | 0.727 |   0.261 |  1.767 |      0.705 |        0.148 |         1 |        0.483 |           0.021 |
| ('pca_logreg_pooled', 'Carboplatin', 'NK')       |   0.721 |        nan | 0.706 | 0.736 |   0.171 |  2.044 |      0.708 |        0.083 |         1 |        0.487 |           0.02  |
| ('pca_logreg_pooled', 'Carboplatin', 'Olaparib') |   0.74  |        nan | 0.723 | 0.756 |   0.219 |  2.273 |      0.709 |        0.096 |         1 |        0.491 |           0.031 |
| ('pca_logreg_pooled', 'Control', 'Carboplatin')  |   0.743 |        nan | 0.726 | 0.76  |   0.19  |  2.31  |      0.712 |        0.082 |         1 |        0.49  |           0.023 |
| ('pca_logreg_pooled', 'Control', 'NK')           |   0.721 |        nan | 0.706 | 0.736 |   0.171 |  2.044 |      0.708 |        0.083 |         1 |        0.524 |           0.022 |
| ('pca_logreg_pooled', 'Control', 'Olaparib')     |   0.74  |        nan | 0.723 | 0.756 |   0.219 |  2.273 |      0.709 |        0.096 |         1 |        0.433 |           0.016 |
| ('pca_logreg_pooled', 'NK', 'Carboplatin')       |   0.743 |        nan | 0.726 | 0.76  |   0.19  |  2.31  |      0.712 |        0.082 |         1 |        0.512 |           0.022 |
| ('pca_logreg_pooled', 'NK', 'Control')           |   0.704 |        nan | 0.682 | 0.727 |   0.261 |  1.767 |      0.705 |        0.148 |         1 |        0.524 |           0.014 |
| ('pca_logreg_pooled', 'NK', 'Olaparib')          |   0.74  |        nan | 0.723 | 0.756 |   0.219 |  2.273 |      0.709 |        0.096 |         1 |        0.518 |           0.025 |
| ('pca_logreg_pooled', 'Olaparib', 'Carboplatin') |   0.743 |        nan | 0.726 | 0.76  |   0.19  |  2.31  |      0.712 |        0.082 |         1 |        0.518 |           0.017 |
| ('pca_logreg_pooled', 'Olaparib', 'Control')     |   0.704 |        nan | 0.682 | 0.727 |   0.261 |  1.767 |      0.705 |        0.148 |         1 |        0.466 |           0.022 |
| ('pca_logreg_pooled', 'Olaparib', 'NK')          |   0.721 |        nan | 0.706 | 0.736 |   0.171 |  2.044 |      0.708 |        0.083 |         1 |        0.548 |           0.012 |
| ('pca_logreg_tuned', 'Carboplatin', 'Control')   |   0.699 |        nan | 0.676 | 0.722 |   0.255 |  1.725 |      0.697 |        0.148 |         1 |        0.496 |         nan     |
| ('pca_logreg_tuned', 'Carboplatin', 'NK')        |   0.712 |        nan | 0.696 | 0.728 |   0.167 |  1.996 |      0.704 |        0.083 |         1 |        0.479 |         nan     |
| ('pca_logreg_tuned', 'Carboplatin', 'Olaparib')  |   0.731 |        nan | 0.713 | 0.748 |   0.217 |  2.253 |      0.697 |        0.096 |         1 |        0.532 |         nan     |
| ('pca_logreg_tuned', 'Control', 'Carboplatin')   |   0.726 |        nan | 0.709 | 0.743 |   0.172 |  2.091 |      0.706 |        0.082 |         1 |        0.502 |         nan     |
| ('pca_logreg_tuned', 'Control', 'NK')            |   0.699 |        nan | 0.682 | 0.715 |   0.15  |  1.793 |      0.69  |        0.083 |         1 |        0.464 |         nan     |
| ('pca_logreg_tuned', 'Control', 'Olaparib')      |   0.711 |        nan | 0.695 | 0.728 |   0.185 |  1.917 |      0.687 |        0.096 |         1 |        0.422 |         nan     |
| ('pca_logreg_tuned', 'NK', 'Carboplatin')        |   0.73  |        nan | 0.711 | 0.748 |   0.18  |  2.187 |      0.703 |        0.082 |         1 |        0.492 |         nan     |
| ('pca_logreg_tuned', 'NK', 'Control')            |   0.696 |        nan | 0.673 | 0.719 |   0.245 |  1.658 |      0.695 |        0.148 |         1 |        0.472 |         nan     |
| ('pca_logreg_tuned', 'NK', 'Olaparib')           |   0.732 |        nan | 0.715 | 0.751 |   0.216 |  2.242 |      0.705 |        0.096 |         1 |        0.556 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'Carboplatin')  |   0.737 |        nan | 0.718 | 0.754 |   0.185 |  2.256 |      0.704 |        0.082 |         1 |        0.471 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'Control')      |   0.692 |        nan | 0.668 | 0.715 |   0.262 |  1.775 |      0.696 |        0.148 |         1 |        0.423 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'NK')           |   0.712 |        nan | 0.696 | 0.728 |   0.169 |  2.022 |      0.701 |        0.083 |         1 |        0.535 |         nan     |
| ('pca_smooth_logreg', 'Carboplatin', 'Control')  |   0.698 |        nan | 0.675 | 0.722 |   0.262 |  1.776 |      0.697 |        0.148 |         1 |        0.485 |           0.021 |
| ('pca_smooth_logreg', 'Carboplatin', 'NK')       |   0.712 |        nan | 0.695 | 0.728 |   0.169 |  2.028 |      0.701 |        0.083 |         1 |        0.502 |           0.027 |
| ('pca_smooth_logreg', 'Carboplatin', 'Olaparib') |   0.736 |        nan | 0.718 | 0.755 |   0.22  |  2.287 |      0.702 |        0.096 |         1 |        0.503 |           0.042 |
| ('pca_smooth_logreg', 'Control', 'Carboplatin')  |   0.728 |        nan | 0.71  | 0.747 |   0.173 |  2.1   |      0.708 |        0.082 |         1 |        0.499 |           0.045 |
| ('pca_smooth_logreg', 'Control', 'NK')           |   0.697 |        nan | 0.68  | 0.714 |   0.153 |  1.835 |      0.686 |        0.083 |         1 |        0.508 |           0.024 |
| ('pca_smooth_logreg', 'Control', 'Olaparib')     |   0.715 |        nan | 0.699 | 0.733 |   0.192 |  1.993 |      0.689 |        0.096 |         1 |        0.519 |           0.065 |
| ('pca_smooth_logreg', 'NK', 'Carboplatin')       |   0.735 |        nan | 0.715 | 0.753 |   0.184 |  2.239 |      0.709 |        0.082 |         1 |        0.501 |           0.034 |
| ('pca_smooth_logreg', 'NK', 'Control')           |   0.693 |        nan | 0.669 | 0.717 |   0.248 |  1.682 |      0.693 |        0.148 |         1 |        0.518 |           0.027 |
| ('pca_smooth_logreg', 'NK', 'Olaparib')          |   0.735 |        nan | 0.718 | 0.753 |   0.22  |  2.281 |      0.705 |        0.096 |         1 |        0.499 |           0.052 |
| ('pca_smooth_logreg', 'Olaparib', 'Carboplatin') |   0.742 |        nan | 0.722 | 0.76  |   0.191 |  2.326 |      0.707 |        0.082 |         1 |        0.512 |           0.029 |
| ('pca_smooth_logreg', 'Olaparib', 'Control')     |   0.69  |        nan | 0.666 | 0.715 |   0.263 |  1.778 |      0.693 |        0.148 |         1 |        0.499 |           0.039 |
| ('pca_smooth_logreg', 'Olaparib', 'NK')          |   0.71  |        nan | 0.695 | 0.727 |   0.171 |  2.044 |      0.696 |        0.083 |         1 |        0.507 |           0.04  |


## cross-arm matrix (pca_logreg)

| train       |   Carboplatin |   Olaparib |    NK |   Control |
|:------------|--------------:|-----------:|------:|----------:|
| Carboplatin |         0.748 |      0.731 | 0.712 |     0.698 |
| Olaparib    |         0.737 |      0.743 | 0.712 |     0.693 |
| NK          |         0.73  |      0.732 | 0.725 |     0.695 |
| Control     |         0.725 |      0.711 | 0.7   |     0.707 |


## fitness confound

| drug_arm    |   n_drug |   prev_drug |   n_control |   prev_control |   auroc_drug_model_on_drug |   auroc_fitness_model_on_drug |   auroc_control_model_on_control |   auroc_drug_model_on_control |   specificity_index |   auroc_drug_model_size_matched |   auroc_fitness_model_same_cells |   specificity_index_size_matched |   auroc_drug_residual_on_drug |   auroc_drug_within_fitness_quintiles |   corr_drug_vs_fitness_score |   lrt_stat |   lrt_p | features   | cc_mode   |
|:------------|---------:|------------:|------------:|---------------:|---------------------------:|------------------------------:|---------------------------------:|------------------------------:|--------------------:|--------------------------------:|---------------------------------:|---------------------------------:|------------------------------:|--------------------------------------:|-----------------------------:|-----------:|--------:|:-----------|:----------|
| Carboplatin |     8942 |      0.0822 |        4183 |         0.1477 |                     0.7484 |                        0.7253 |                           0.7066 |                        0.6983 |              0.023  |                          0.739  |                           0.7225 |                           0.0164 |                        0.5982 |                                0.651  |                       0.8189 |    116.542 |       0 | pca        | regress   |
| Olaparib    |     9394 |      0.0962 |        4183 |         0.1477 |                     0.7432 |                        0.7114 |                           0.7066 |                        0.6927 |              0.0318 |                          0.7401 |                           0.7115 |                           0.0287 |                        0.64   |                                0.6549 |                       0.7962 |    163.863 |       0 | pca        | regress   |
| NK          |    10123 |      0.0835 |        4183 |         0.1477 |                     0.7246 |                        0.6996 |                           0.7066 |                        0.6954 |              0.0251 |                          0.7143 |                           0.7015 |                           0.0128 |                        0.5978 |                                0.6448 |                       0.8172 |    120.597 |       0 | pca        | regress   |


## ceiling decomposition (pi=0.1)

| model            | arm         |   pi |   auroc_oof |   rho_obs |   rho_fate | saturated   |   auroc_if_sister_seen |   sister_cost |
|:-----------------|:------------|-----:|------------:|----------:|-----------:|:------------|-----------------------:|--------------:|
| pca_logreg_tuned | Carboplatin |  0.1 |       0.748 |     0.497 |      0.69  | False       |                  0.836 |         0.088 |
| pca_logreg_tuned | Control     |  0.1 |       0.707 |     0.449 |      0.558 | False       |                  0.757 |         0.05  |
| pca_logreg_tuned | NK          |  0.1 |       0.725 |     0.451 |      0.701 | False       |                  0.84  |         0.116 |
| pca_logreg_tuned | Olaparib    |  0.1 |       0.743 |     0.498 |      0.704 | False       |                  0.837 |         0.094 |


## ceiling_regress.csv

| arm         |   prevalence |   rho |   pi |   auroc_ceiling | cc_mode   |
|:------------|-------------:|------:|-----:|----------------:|:----------|
| Carboplatin |        0.082 | 0.928 |  0   |           0.976 | regress   |
| Carboplatin |        0.082 | 0.928 |  0.1 |           0.928 | regress   |
| Carboplatin |        0.082 | 0.928 |  0.2 |           0.881 | regress   |
| Olaparib    |        0.096 | 0.928 |  0   |           0.974 | regress   |
| Olaparib    |        0.096 | 0.928 |  0.1 |           0.927 | regress   |
| Olaparib    |        0.096 | 0.928 |  0.2 |           0.879 | regress   |
| NK          |        0.083 | 0.928 |  0   |           0.976 | regress   |
| NK          |        0.083 | 0.928 |  0.1 |           0.928 | regress   |
| NK          |        0.083 | 0.928 |  0.2 |           0.88  | regress   |
| Control     |        0.148 | 0.928 |  0   |           0.968 | regress   |
| Control     |        0.148 | 0.928 |  0.1 |           0.921 | regress   |
| Control     |        0.148 | 0.928 |  0.2 |           0.875 | regress   |


## external_validation.csv

| dataset       | analysis                 | label       | subset    | model                  |   n_test |   n_pos |   prevalence |   auroc |   auprc |   auprc_lift |   auroc_lo |   auroc_hi |   auprc_lo |   auprc_hi | config_hash   |
|:--------------|:-------------------------|:------------|:----------|:-----------------------|---------:|--------:|-------------:|--------:|--------:|-------------:|-----------:|-----------:|-----------:|-----------:|:--------------|
| watermelon    | within_external          | y_persister | all       | clone_size             |     5087 |    3172 |        0.624 |   0.759 |   0.843 |        1.352 |      0.735 |      0.779 |      0.81  |      0.87  | cc5d35e4      |
| watermelon    | within_external          | y_persister | all       | covariates             |     5087 |    3172 |        0.624 |   0.57  |   0.662 |        1.061 |      0.552 |      0.588 |      0.635 |      0.686 | cc5d35e4      |
| watermelon    | within_external          | y_persister | all       | pca                    |     5087 |    3172 |        0.624 |   0.609 |   0.707 |        1.134 |      0.59  |      0.63  |      0.682 |      0.734 | cc5d35e4      |
| watermelon    | within_external          | y_persister | all       | pca+clone_size         |     5087 |    3172 |        0.624 |   0.77  |   0.852 |        1.366 |      0.747 |      0.791 |      0.82  |      0.879 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | all       | trained_on_Carboplatin |     5087 |    3172 |        0.624 |   0.5   |   0.628 |        1.007 |      0.483 |      0.519 |      0.601 |      0.656 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | all       | trained_on_Olaparib    |     5087 |    3172 |        0.624 |   0.51  |   0.628 |        1.008 |      0.49  |      0.528 |      0.601 |      0.654 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | all       | trained_on_NK          |     5087 |    3172 |        0.624 |   0.518 |   0.634 |        1.017 |      0.5   |      0.532 |      0.609 |      0.662 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | all       | trained_on_Control     |     5087 |    3172 |        0.624 |   0.491 |   0.617 |        0.99  |      0.475 |      0.509 |      0.59  |      0.643 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | all       | trained_on_all_drugs   |     5087 |    3172 |        0.624 |   0.506 |   0.626 |        1.003 |      0.489 |      0.522 |      0.6   |      0.651 | cc5d35e4      |
| watermelon    | within_external          | y_persister | singleton | covariates             |     2099 |     810 |        0.386 |   0.583 |   0.439 |        1.137 |      0.559 |      0.606 |      0.409 |      0.472 | cc5d35e4      |
| watermelon    | within_external          | y_persister | singleton | pca                    |     2099 |     810 |        0.386 |   0.582 |   0.456 |        1.181 |      0.556 |      0.605 |      0.428 |      0.491 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | singleton | trained_on_Carboplatin |     2099 |     810 |        0.386 |   0.486 |   0.385 |        0.998 |      0.463 |      0.509 |      0.36  |      0.417 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | singleton | trained_on_Olaparib    |     2099 |     810 |        0.386 |   0.499 |   0.389 |        1.008 |      0.476 |      0.524 |      0.364 |      0.421 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | singleton | trained_on_NK          |     2099 |     810 |        0.386 |   0.514 |   0.393 |        1.019 |      0.491 |      0.538 |      0.368 |      0.423 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | singleton | trained_on_Control     |     2099 |     810 |        0.386 |   0.504 |   0.384 |        0.995 |      0.477 |      0.53  |      0.36  |      0.416 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_persister | singleton | trained_on_all_drugs   |     2099 |     810 |        0.386 |   0.495 |   0.38  |        0.984 |      0.471 |      0.517 |      0.358 |      0.409 | cc5d35e4      |
| watermelon    | within_external          | y_cycling   | all       | clone_size             |     5087 |    2373 |        0.466 |   0.666 |   0.615 |        1.319 |      0.634 |      0.699 |      0.557 |      0.676 | cc5d35e4      |
| watermelon    | within_external          | y_cycling   | all       | covariates             |     5087 |    2373 |        0.466 |   0.537 |   0.484 |        1.038 |      0.52  |      0.553 |      0.457 |      0.516 | cc5d35e4      |
| watermelon    | within_external          | y_cycling   | all       | pca                    |     5087 |    2373 |        0.466 |   0.545 |   0.503 |        1.079 |      0.526 |      0.564 |      0.475 |      0.536 | cc5d35e4      |
| watermelon    | within_external          | y_cycling   | all       | pca+clone_size         |     5087 |    2373 |        0.466 |   0.668 |   0.636 |        1.364 |      0.641 |      0.696 |      0.581 |      0.686 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | all       | trained_on_Carboplatin |     5087 |    2373 |        0.466 |   0.504 |   0.478 |        1.024 |      0.489 |      0.522 |      0.45  |      0.507 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | all       | trained_on_Olaparib    |     5087 |    2373 |        0.466 |   0.501 |   0.467 |        1     |      0.486 |      0.516 |      0.438 |      0.498 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | all       | trained_on_NK          |     5087 |    2373 |        0.466 |   0.503 |   0.463 |        0.993 |      0.488 |      0.519 |      0.432 |      0.492 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | all       | trained_on_Control     |     5087 |    2373 |        0.466 |   0.489 |   0.459 |        0.984 |      0.476 |      0.506 |      0.433 |      0.491 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | all       | trained_on_all_drugs   |     5087 |    2373 |        0.466 |   0.502 |   0.464 |        0.995 |      0.488 |      0.519 |      0.436 |      0.494 | cc5d35e4      |
| watermelon    | within_external          | y_cycling   | singleton | covariates             |     2099 |     622 |        0.296 |   0.556 |   0.327 |        1.104 |      0.532 |      0.582 |      0.298 |      0.361 | cc5d35e4      |
| watermelon    | within_external          | y_cycling   | singleton | pca                    |     2099 |     622 |        0.296 |   0.529 |   0.317 |        1.071 |      0.504 |      0.556 |      0.288 |      0.353 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | singleton | trained_on_Carboplatin |     2099 |     622 |        0.296 |   0.493 |   0.3   |        1.014 |      0.468 |      0.519 |      0.274 |      0.335 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | singleton | trained_on_Olaparib    |     2099 |     622 |        0.296 |   0.493 |   0.293 |        0.989 |      0.464 |      0.516 |      0.268 |      0.324 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | singleton | trained_on_NK          |     2099 |     622 |        0.296 |   0.504 |   0.298 |        1.005 |      0.475 |      0.528 |      0.272 |      0.329 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | singleton | trained_on_Control     |     2099 |     622 |        0.296 |   0.5   |   0.294 |        0.991 |      0.47  |      0.526 |      0.266 |      0.323 | cc5d35e4      |
| watermelon    | transfer_from_resistrace | y_cycling   | singleton | trained_on_all_drugs   |     2099 |     622 |        0.296 |   0.498 |   0.292 |        0.985 |      0.47  |      0.525 |      0.268 |      0.324 | cc5d35e4      |
| tnbc_afatinib | within_external          | y_persister | all       | clone_size             |     1541 |     861 |        0.559 |   0.877 |   0.913 |        1.634 |      0.787 |      0.928 |      0.746 |      0.968 | cc5d35e4      |
| tnbc_afatinib | within_external          | y_persister | all       | covariates             |     1541 |     861 |        0.559 |   0.488 |   0.549 |        0.983 |      0.447 |      0.539 |      0.398 |      0.662 | cc5d35e4      |
| tnbc_afatinib | within_external          | y_persister | all       | pca                    |     1541 |     861 |        0.559 |   0.635 |   0.687 |        1.229 |      0.535 |      0.706 |      0.479 |      0.808 | cc5d35e4      |
| tnbc_afatinib | within_external          | y_persister | all       | pca+clone_size         |     1541 |     861 |        0.559 |   0.877 |   0.918 |        1.642 |      0.788 |      0.927 |      0.763 |      0.969 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | all       | trained_on_Carboplatin |     1541 |     861 |        0.559 |   0.54  |   0.586 |        1.049 |      0.501 |      0.575 |      0.435 |      0.695 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | all       | trained_on_Olaparib    |     1541 |     861 |        0.559 |   0.57  |   0.607 |        1.087 |      0.514 |      0.608 |      0.429 |      0.722 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | all       | trained_on_NK          |     1541 |     861 |        0.559 |   0.536 |   0.582 |        1.042 |      0.508 |      0.565 |      0.443 |      0.686 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | all       | trained_on_Control     |     1541 |     861 |        0.559 |   0.544 |   0.597 |        1.068 |      0.518 |      0.582 |      0.463 |      0.695 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | all       | trained_on_all_drugs   |     1541 |     861 |        0.559 |   0.542 |   0.591 |        1.058 |      0.504 |      0.572 |      0.434 |      0.703 | cc5d35e4      |
| tnbc_afatinib | within_external          | y_persister | singleton | covariates             |      237 |      27 |        0.114 |   0.422 |   0.097 |        0.854 |      0.311 |      0.525 |      0.066 |      0.149 | cc5d35e4      |
| tnbc_afatinib | within_external          | y_persister | singleton | pca                    |      237 |      27 |        0.114 |   0.561 |   0.153 |        1.345 |      0.425 |      0.684 |      0.089 |      0.271 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | singleton | trained_on_Carboplatin |      237 |      27 |        0.114 |   0.516 |   0.147 |        1.29  |      0.41  |      0.627 |      0.088 |      0.302 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | singleton | trained_on_Olaparib    |      237 |      27 |        0.114 |   0.525 |   0.131 |        1.147 |      0.421 |      0.626 |      0.083 |      0.224 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | singleton | trained_on_NK          |      237 |      27 |        0.114 |   0.6   |   0.151 |        1.327 |      0.489 |      0.706 |      0.098 |      0.252 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | singleton | trained_on_Control     |      237 |      27 |        0.114 |   0.642 |   0.183 |        1.603 |      0.53  |      0.757 |      0.106 |      0.306 | cc5d35e4      |
| tnbc_afatinib | transfer_from_resistrace | y_persister | singleton | trained_on_all_drugs   |      237 |      27 |        0.114 |   0.582 |   0.129 |        1.134 |      0.501 |      0.689 |      0.087 |      0.19  | cc5d35e4      |
