# PERSIST results summary (cc_mode=regress_all)


## within

|                                                     |   auroc |   auroc_sd |    lo |    hi |   auprc |   lift |   wc_auroc |   prevalence |   n_seeds |   auroc_shuf |   auroc_shuf_sd |
|:----------------------------------------------------|--------:|-----------:|------:|------:|--------:|-------:|-----------:|-------------:|----------:|-------------:|----------------:|
| ('cov_logreg', 'Carboplatin', 'Carboplatin')        |   0.613 |        nan | 0.592 | 0.632 |   0.107 |  1.307 |      0.609 |        0.082 |         1 |        0.478 |           0.018 |
| ('cov_logreg', 'Control', 'Control')                |   0.589 |        nan | 0.566 | 0.611 |   0.172 |  1.165 |      0.592 |        0.148 |         1 |        0.484 |           0.018 |
| ('cov_logreg', 'NK', 'NK')                          |   0.651 |        nan | 0.631 | 0.668 |   0.123 |  1.469 |      0.65  |        0.083 |         1 |        0.498 |           0.018 |
| ('cov_logreg', 'Olaparib', 'Olaparib')              |   0.596 |        nan | 0.579 | 0.612 |   0.113 |  1.177 |      0.584 |        0.096 |         1 |        0.509 |           0.026 |
| ('hvg_logreg', 'Carboplatin', 'Carboplatin')        |   0.62  |        nan | 0.6   | 0.64  |   0.117 |  1.421 |      0.598 |        0.082 |         1 |        0.521 |           0.013 |
| ('hvg_logreg', 'Control', 'Control')                |   0.623 |        nan | 0.598 | 0.644 |   0.199 |  1.345 |      0.61  |        0.148 |         1 |        0.528 |           0.014 |
| ('hvg_logreg', 'NK', 'NK')                          |   0.594 |        nan | 0.575 | 0.614 |   0.115 |  1.379 |      0.579 |        0.083 |         1 |        0.517 |           0.006 |
| ('hvg_logreg', 'Olaparib', 'Olaparib')              |   0.642 |        nan | 0.622 | 0.66  |   0.146 |  1.515 |      0.614 |        0.096 |         1 |        0.516 |           0.013 |
| ('mlp', 'Carboplatin', 'Carboplatin')               |   0.723 |        nan | 0.7   | 0.742 |   0.178 |  2.171 |      0.687 |        0.082 |         1 |      nan     |         nan     |
| ('mlp', 'Control', 'Control')                       |   0.697 |        nan | 0.672 | 0.719 |   0.262 |  1.77  |      0.68  |        0.148 |         1 |      nan     |         nan     |
| ('mlp', 'NK', 'NK')                                 |   0.685 |        nan | 0.667 | 0.703 |   0.156 |  1.865 |      0.671 |        0.083 |         1 |      nan     |         nan     |
| ('mlp', 'Olaparib', 'Olaparib')                     |   0.722 |        nan | 0.704 | 0.741 |   0.203 |  2.112 |      0.681 |        0.096 |         1 |      nan     |         nan     |
| ('pca_logreg', 'Carboplatin', 'Carboplatin')        |   0.723 |        nan | 0.705 | 0.742 |   0.181 |  2.203 |      0.688 |        0.082 |         1 |        0.508 |           0.016 |
| ('pca_logreg', 'Control', 'Control')                |   0.704 |        nan | 0.681 | 0.724 |   0.252 |  1.704 |      0.689 |        0.148 |         1 |        0.523 |           0.028 |
| ('pca_logreg', 'NK', 'NK')                          |   0.68  |        nan | 0.662 | 0.697 |   0.149 |  1.781 |      0.664 |        0.083 |         1 |        0.487 |           0.019 |
| ('pca_logreg', 'Olaparib', 'Olaparib')              |   0.727 |        nan | 0.71  | 0.745 |   0.204 |  2.119 |      0.69  |        0.096 |         1 |        0.51  |           0.015 |
| ('pca_logreg_pooled', 'Carboplatin', 'Carboplatin') |   0.725 |        nan | 0.708 | 0.743 |   0.182 |  2.21  |      0.691 |        0.082 |         1 |        0.51  |           0.005 |
| ('pca_logreg_pooled', 'Control', 'Control')         |   0.707 |        nan | 0.684 | 0.729 |   0.268 |  1.815 |      0.7   |        0.148 |         1 |        0.48  |           0.01  |
| ('pca_logreg_pooled', 'NK', 'NK')                   |   0.684 |        nan | 0.667 | 0.701 |   0.156 |  1.869 |      0.673 |        0.083 |         1 |        0.557 |           0.007 |
| ('pca_logreg_pooled', 'Olaparib', 'Olaparib')       |   0.73  |        nan | 0.713 | 0.747 |   0.203 |  2.114 |      0.698 |        0.096 |         1 |        0.525 |           0.006 |
| ('pca_logreg_tuned', 'Carboplatin', 'Carboplatin')  |   0.72  |        nan | 0.701 | 0.739 |   0.177 |  2.154 |      0.687 |        0.082 |         1 |        0.533 |         nan     |
| ('pca_logreg_tuned', 'Control', 'Control')          |   0.704 |        nan | 0.681 | 0.725 |   0.252 |  1.707 |      0.69  |        0.148 |         1 |        0.529 |         nan     |
| ('pca_logreg_tuned', 'NK', 'NK')                    |   0.672 |        nan | 0.653 | 0.689 |   0.144 |  1.729 |      0.656 |        0.083 |         1 |        0.516 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'Olaparib')        |   0.727 |        nan | 0.709 | 0.745 |   0.205 |  2.13  |      0.689 |        0.096 |         1 |        0.479 |         nan     |
| ('pca_smooth_logreg', 'Carboplatin', 'Carboplatin') |   0.729 |        nan | 0.71  | 0.748 |   0.187 |  2.281 |      0.691 |        0.082 |         1 |        0.505 |           0.015 |
| ('pca_smooth_logreg', 'Control', 'Control')         |   0.702 |        nan | 0.678 | 0.724 |   0.252 |  1.704 |      0.683 |        0.148 |         1 |        0.51  |           0.011 |
| ('pca_smooth_logreg', 'NK', 'NK')                   |   0.683 |        nan | 0.666 | 0.701 |   0.151 |  1.806 |      0.666 |        0.083 |         1 |        0.496 |           0.024 |
| ('pca_smooth_logreg', 'Olaparib', 'Olaparib')       |   0.731 |        nan | 0.714 | 0.749 |   0.208 |  2.158 |      0.691 |        0.096 |         1 |        0.514 |           0.019 |
| ('persist_gnn', 'Carboplatin', 'Carboplatin')       |   0.721 |        nan | 0.699 | 0.74  |   0.189 |  2.305 |      0.684 |        0.082 |         1 |      nan     |         nan     |
| ('persist_gnn', 'Control', 'Control')               |   0.689 |        nan | 0.664 | 0.711 |   0.26  |  1.763 |      0.662 |        0.148 |         1 |      nan     |         nan     |
| ('persist_gnn', 'NK', 'NK')                         |   0.664 |        nan | 0.644 | 0.682 |   0.148 |  1.768 |      0.644 |        0.083 |         1 |      nan     |         nan     |
| ('persist_gnn', 'Olaparib', 'Olaparib')             |   0.716 |        nan | 0.697 | 0.735 |   0.193 |  2.003 |      0.665 |        0.096 |         1 |      nan     |         nan     |


## rep_holdout

|                                                         |   auroc |   auroc_sd |    lo |    hi |   auprc |   lift |   wc_auroc |   prevalence |   n_seeds |   auroc_shuf |   auroc_shuf_sd |
|:--------------------------------------------------------|--------:|-----------:|------:|------:|--------:|-------:|-----------:|-------------:|----------:|-------------:|----------------:|
| ('cov_logreg', 'Carboplatin_1', 'Carboplatin_2')        |   0.626 |        nan | 0.599 | 0.655 |   0.119 |  1.383 |      0.635 |        0.086 |         1 |        0.49  |           0.078 |
| ('cov_logreg', 'Carboplatin_2', 'Carboplatin_1')        |   0.613 |        nan | 0.586 | 0.64  |   0.1   |  1.278 |      0.6   |        0.078 |         1 |        0.502 |           0.067 |
| ('cov_logreg', 'Control_1', 'Control_2')                |   0.589 |        nan | 0.548 | 0.628 |   0.172 |  1.154 |      0.592 |        0.149 |         1 |        0.521 |           0.035 |
| ('cov_logreg', 'Control_2', 'Control_1')                |   0.595 |        nan | 0.564 | 0.626 |   0.174 |  1.183 |      0.6   |        0.147 |         1 |        0.496 |           0.048 |
| ('cov_logreg', 'NK_1', 'NK_2')                          |   0.664 |        nan | 0.645 | 0.687 |   0.124 |  1.508 |      0.662 |        0.082 |         1 |        0.43  |           0.031 |
| ('cov_logreg', 'NK_2', 'NK_1')                          |   0.627 |        nan | 0.594 | 0.653 |   0.119 |  1.4   |      0.623 |        0.085 |         1 |        0.513 |           0.066 |
| ('cov_logreg', 'Olaparib_1', 'Olaparib_2')              |   0.588 |        nan | 0.561 | 0.613 |   0.095 |  1.181 |      0.568 |        0.08  |         1 |        0.469 |           0.048 |
| ('cov_logreg', 'Olaparib_2', 'Olaparib_1')              |   0.6   |        nan | 0.575 | 0.625 |   0.132 |  1.18  |      0.592 |        0.112 |         1 |        0.487 |           0.083 |
| ('hvg_logreg', 'Carboplatin_1', 'Carboplatin_2')        |   0.626 |        nan | 0.6   | 0.653 |   0.127 |  1.474 |      0.595 |        0.086 |         1 |        0.516 |           0.019 |
| ('hvg_logreg', 'Carboplatin_2', 'Carboplatin_1')        |   0.617 |        nan | 0.586 | 0.647 |   0.121 |  1.544 |      0.586 |        0.078 |         1 |        0.525 |           0.016 |
| ('hvg_logreg', 'Control_1', 'Control_2')                |   0.652 |        nan | 0.621 | 0.682 |   0.208 |  1.394 |      0.639 |        0.149 |         1 |        0.519 |           0.025 |
| ('hvg_logreg', 'Control_2', 'Control_1')                |   0.65  |        nan | 0.62  | 0.683 |   0.223 |  1.521 |      0.636 |        0.147 |         1 |        0.512 |           0.012 |
| ('hvg_logreg', 'NK_1', 'NK_2')                          |   0.579 |        nan | 0.552 | 0.601 |   0.106 |  1.286 |      0.566 |        0.082 |         1 |        0.512 |           0.018 |
| ('hvg_logreg', 'NK_2', 'NK_1')                          |   0.589 |        nan | 0.556 | 0.623 |   0.111 |  1.296 |      0.577 |        0.085 |         1 |        0.505 |           0.009 |
| ('hvg_logreg', 'Olaparib_1', 'Olaparib_2')              |   0.631 |        nan | 0.597 | 0.66  |   0.118 |  1.476 |      0.598 |        0.08  |         1 |        0.528 |           0.025 |
| ('hvg_logreg', 'Olaparib_2', 'Olaparib_1')              |   0.625 |        nan | 0.601 | 0.649 |   0.159 |  1.419 |      0.602 |        0.112 |         1 |        0.52  |           0.011 |
| ('pca_logreg', 'Carboplatin_1', 'Carboplatin_2')        |   0.713 |        nan | 0.683 | 0.74  |   0.187 |  2.165 |      0.683 |        0.086 |         1 |        0.448 |           0.021 |
| ('pca_logreg', 'Carboplatin_2', 'Carboplatin_1')        |   0.711 |        nan | 0.679 | 0.74  |   0.164 |  2.093 |      0.683 |        0.078 |         1 |        0.516 |           0.052 |
| ('pca_logreg', 'Control_1', 'Control_2')                |   0.694 |        nan | 0.661 | 0.729 |   0.241 |  1.614 |      0.68  |        0.149 |         1 |        0.497 |           0.038 |
| ('pca_logreg', 'Control_2', 'Control_1')                |   0.694 |        nan | 0.663 | 0.724 |   0.252 |  1.718 |      0.681 |        0.147 |         1 |        0.52  |           0.03  |
| ('pca_logreg', 'NK_1', 'NK_2')                          |   0.655 |        nan | 0.63  | 0.68  |   0.135 |  1.634 |      0.644 |        0.082 |         1 |        0.488 |           0.037 |
| ('pca_logreg', 'NK_2', 'NK_1')                          |   0.678 |        nan | 0.649 | 0.708 |   0.153 |  1.788 |      0.66  |        0.085 |         1 |        0.513 |           0.026 |
| ('pca_logreg', 'Olaparib_1', 'Olaparib_2')              |   0.739 |        nan | 0.712 | 0.766 |   0.187 |  2.336 |      0.696 |        0.08  |         1 |        0.522 |           0.03  |
| ('pca_logreg', 'Olaparib_2', 'Olaparib_1')              |   0.72  |        nan | 0.698 | 0.744 |   0.224 |  2.001 |      0.692 |        0.112 |         1 |        0.535 |           0.036 |
| ('pca_logreg_pooled', 'Carboplatin_1', 'Carboplatin_2') |   0.712 |        nan | 0.685 | 0.739 |   0.183 |  2.116 |      0.677 |        0.086 |         1 |        0.52  |           0.011 |
| ('pca_logreg_pooled', 'Carboplatin_2', 'Carboplatin_1') |   0.736 |        nan | 0.706 | 0.762 |   0.18  |  2.305 |      0.709 |        0.078 |         1 |        0.492 |           0.012 |
| ('pca_logreg_pooled', 'Control_1', 'Control_2')         |   0.713 |        nan | 0.683 | 0.74  |   0.26  |  1.746 |      0.701 |        0.149 |         1 |        0.491 |           0.022 |
| ('pca_logreg_pooled', 'Control_2', 'Control_1')         |   0.696 |        nan | 0.665 | 0.725 |   0.284 |  1.935 |      0.692 |        0.147 |         1 |        0.472 |           0.01  |
| ('pca_logreg_pooled', 'NK_1', 'NK_2')                   |   0.675 |        nan | 0.65  | 0.7   |   0.15  |  1.826 |      0.675 |        0.082 |         1 |        0.569 |           0.012 |
| ('pca_logreg_pooled', 'NK_2', 'NK_1')                   |   0.692 |        nan | 0.664 | 0.721 |   0.166 |  1.942 |      0.666 |        0.085 |         1 |        0.554 |           0.015 |
| ('pca_logreg_pooled', 'Olaparib_1', 'Olaparib_2')       |   0.735 |        nan | 0.709 | 0.762 |   0.183 |  2.276 |      0.702 |        0.08  |         1 |        0.513 |           0.036 |
| ('pca_logreg_pooled', 'Olaparib_2', 'Olaparib_1')       |   0.727 |        nan | 0.705 | 0.75  |   0.228 |  2.033 |      0.698 |        0.112 |         1 |        0.516 |           0.017 |
| ('pca_logreg_tuned', 'Carboplatin_1', 'Carboplatin_2')  |   0.716 |        nan | 0.687 | 0.743 |   0.176 |  2.033 |      0.691 |        0.086 |         1 |        0.543 |         nan     |
| ('pca_logreg_tuned', 'Carboplatin_2', 'Carboplatin_1')  |   0.709 |        nan | 0.677 | 0.74  |   0.166 |  2.127 |      0.683 |        0.078 |         1 |        0.552 |         nan     |
| ('pca_logreg_tuned', 'Control_1', 'Control_2')          |   0.693 |        nan | 0.66  | 0.728 |   0.241 |  1.613 |      0.679 |        0.149 |         1 |        0.51  |         nan     |
| ('pca_logreg_tuned', 'Control_2', 'Control_1')          |   0.681 |        nan | 0.649 | 0.715 |   0.253 |  1.727 |      0.67  |        0.147 |         1 |        0.547 |         nan     |
| ('pca_logreg_tuned', 'NK_1', 'NK_2')                    |   0.655 |        nan | 0.629 | 0.68  |   0.134 |  1.628 |      0.643 |        0.082 |         1 |        0.491 |         nan     |
| ('pca_logreg_tuned', 'NK_2', 'NK_1')                    |   0.673 |        nan | 0.644 | 0.704 |   0.154 |  1.806 |      0.657 |        0.085 |         1 |        0.506 |         nan     |
| ('pca_logreg_tuned', 'Olaparib_1', 'Olaparib_2')        |   0.74  |        nan | 0.713 | 0.767 |   0.188 |  2.345 |      0.696 |        0.08  |         1 |        0.449 |         nan     |
| ('pca_logreg_tuned', 'Olaparib_2', 'Olaparib_1')        |   0.719 |        nan | 0.697 | 0.743 |   0.225 |  2.01  |      0.69  |        0.112 |         1 |        0.498 |         nan     |
| ('pca_smooth_logreg', 'Carboplatin_1', 'Carboplatin_2') |   0.716 |        nan | 0.687 | 0.743 |   0.19  |  2.202 |      0.683 |        0.086 |         1 |        0.522 |           0.027 |
| ('pca_smooth_logreg', 'Carboplatin_2', 'Carboplatin_1') |   0.714 |        nan | 0.681 | 0.742 |   0.167 |  2.133 |      0.684 |        0.078 |         1 |        0.514 |           0.028 |
| ('pca_smooth_logreg', 'Control_1', 'Control_2')         |   0.695 |        nan | 0.663 | 0.728 |   0.242 |  1.62  |      0.678 |        0.149 |         1 |        0.521 |           0.043 |
| ('pca_smooth_logreg', 'Control_2', 'Control_1')         |   0.697 |        nan | 0.668 | 0.725 |   0.257 |  1.751 |      0.683 |        0.147 |         1 |        0.522 |           0.025 |
| ('pca_smooth_logreg', 'NK_1', 'NK_2')                   |   0.661 |        nan | 0.637 | 0.688 |   0.138 |  1.681 |      0.65  |        0.082 |         1 |        0.526 |           0.022 |
| ('pca_smooth_logreg', 'NK_2', 'NK_1')                   |   0.673 |        nan | 0.645 | 0.703 |   0.152 |  1.776 |      0.653 |        0.085 |         1 |        0.515 |           0.021 |
| ('pca_smooth_logreg', 'Olaparib_1', 'Olaparib_2')       |   0.743 |        nan | 0.716 | 0.77  |   0.194 |  2.413 |      0.696 |        0.08  |         1 |        0.475 |           0.051 |
| ('pca_smooth_logreg', 'Olaparib_2', 'Olaparib_1')       |   0.725 |        nan | 0.703 | 0.748 |   0.233 |  2.082 |      0.693 |        0.112 |         1 |        0.527 |           0.07  |


## cross_arm

|                                                  |   auroc |   auroc_sd |    lo |    hi |   auprc |   lift |   wc_auroc |   prevalence |   n_seeds |   auroc_shuf |   auroc_shuf_sd |
|:-------------------------------------------------|--------:|-----------:|------:|------:|--------:|-------:|-----------:|-------------:|----------:|-------------:|----------------:|
| ('cov_logreg', 'Carboplatin', 'Control')         |   0.588 |        nan | 0.565 | 0.611 |   0.173 |  1.169 |      0.594 |        0.148 |         1 |        0.498 |           0.039 |
| ('cov_logreg', 'Carboplatin', 'NK')              |   0.654 |        nan | 0.635 | 0.671 |   0.123 |  1.473 |      0.654 |        0.083 |         1 |        0.55  |           0.081 |
| ('cov_logreg', 'Carboplatin', 'Olaparib')        |   0.602 |        nan | 0.585 | 0.62  |   0.117 |  1.214 |      0.592 |        0.096 |         1 |        0.479 |           0.049 |
| ('cov_logreg', 'Control', 'Carboplatin')         |   0.604 |        nan | 0.583 | 0.625 |   0.104 |  1.266 |      0.604 |        0.082 |         1 |        0.476 |           0.036 |
| ('cov_logreg', 'Control', 'NK')                  |   0.633 |        nan | 0.615 | 0.651 |   0.116 |  1.389 |      0.632 |        0.083 |         1 |        0.496 |           0.078 |
| ('cov_logreg', 'Control', 'Olaparib')            |   0.594 |        nan | 0.577 | 0.612 |   0.114 |  1.18  |      0.588 |        0.096 |         1 |        0.492 |           0.069 |
| ('cov_logreg', 'NK', 'Carboplatin')              |   0.611 |        nan | 0.59  | 0.63  |   0.107 |  1.303 |      0.606 |        0.082 |         1 |        0.467 |           0.049 |
| ('cov_logreg', 'NK', 'Control')                  |   0.583 |        nan | 0.561 | 0.606 |   0.17  |  1.149 |      0.588 |        0.148 |         1 |        0.473 |           0.018 |
| ('cov_logreg', 'NK', 'Olaparib')                 |   0.603 |        nan | 0.585 | 0.62  |   0.117 |  1.212 |      0.59  |        0.096 |         1 |        0.499 |           0.019 |
| ('cov_logreg', 'Olaparib', 'Carboplatin')        |   0.599 |        nan | 0.578 | 0.62  |   0.104 |  1.267 |      0.594 |        0.082 |         1 |        0.489 |           0.041 |
| ('cov_logreg', 'Olaparib', 'Control')            |   0.578 |        nan | 0.556 | 0.601 |   0.167 |  1.133 |      0.584 |        0.148 |         1 |        0.552 |           0.045 |
| ('cov_logreg', 'Olaparib', 'NK')                 |   0.646 |        nan | 0.629 | 0.664 |   0.121 |  1.454 |      0.645 |        0.083 |         1 |        0.549 |           0.082 |
| ('hvg_logreg', 'Carboplatin', 'Control')         |   0.622 |        nan | 0.601 | 0.646 |   0.205 |  1.388 |      0.607 |        0.148 |         1 |        0.525 |           0.017 |
| ('hvg_logreg', 'Carboplatin', 'NK')              |   0.628 |        nan | 0.607 | 0.648 |   0.126 |  1.507 |      0.618 |        0.083 |         1 |        0.517 |           0.009 |
| ('hvg_logreg', 'Carboplatin', 'Olaparib')        |   0.647 |        nan | 0.628 | 0.663 |   0.148 |  1.536 |      0.623 |        0.096 |         1 |        0.528 |           0.011 |
| ('hvg_logreg', 'Control', 'Carboplatin')         |   0.631 |        nan | 0.611 | 0.652 |   0.122 |  1.49  |      0.615 |        0.082 |         1 |        0.509 |           0.012 |
| ('hvg_logreg', 'Control', 'NK')                  |   0.592 |        nan | 0.574 | 0.613 |   0.111 |  1.333 |      0.586 |        0.083 |         1 |        0.513 |           0.011 |
| ('hvg_logreg', 'Control', 'Olaparib')            |   0.634 |        nan | 0.616 | 0.652 |   0.141 |  1.47  |      0.613 |        0.096 |         1 |        0.522 |           0.007 |
| ('hvg_logreg', 'NK', 'Carboplatin')              |   0.638 |        nan | 0.618 | 0.657 |   0.129 |  1.571 |      0.626 |        0.082 |         1 |        0.529 |           0.007 |
| ('hvg_logreg', 'NK', 'Control')                  |   0.621 |        nan | 0.598 | 0.641 |   0.204 |  1.378 |      0.613 |        0.148 |         1 |        0.514 |           0.016 |
| ('hvg_logreg', 'NK', 'Olaparib')                 |   0.615 |        nan | 0.596 | 0.632 |   0.134 |  1.387 |      0.604 |        0.096 |         1 |        0.521 |           0.009 |
| ('hvg_logreg', 'Olaparib', 'Carboplatin')        |   0.666 |        nan | 0.647 | 0.686 |   0.142 |  1.73  |      0.637 |        0.082 |         1 |        0.513 |           0.011 |
| ('hvg_logreg', 'Olaparib', 'Control')            |   0.629 |        nan | 0.605 | 0.656 |   0.209 |  1.418 |      0.613 |        0.148 |         1 |        0.515 |           0.011 |
| ('hvg_logreg', 'Olaparib', 'NK')                 |   0.622 |        nan | 0.602 | 0.641 |   0.131 |  1.571 |      0.61  |        0.083 |         1 |        0.511 |           0.009 |
| ('pca_logreg', 'Carboplatin', 'Control')         |   0.694 |        nan | 0.671 | 0.717 |   0.26  |  1.761 |      0.688 |        0.148 |         1 |        0.498 |           0.029 |
| ('pca_logreg', 'Carboplatin', 'NK')              |   0.669 |        nan | 0.651 | 0.686 |   0.149 |  1.78  |      0.666 |        0.083 |         1 |        0.514 |           0.035 |
| ('pca_logreg', 'Carboplatin', 'Olaparib')        |   0.717 |        nan | 0.7   | 0.737 |   0.195 |  2.022 |      0.685 |        0.096 |         1 |        0.488 |           0.019 |
| ('pca_logreg', 'Control', 'Carboplatin')         |   0.703 |        nan | 0.685 | 0.722 |   0.157 |  1.914 |      0.682 |        0.082 |         1 |        0.545 |           0.03  |
| ('pca_logreg', 'Control', 'NK')                  |   0.664 |        nan | 0.644 | 0.683 |   0.135 |  1.621 |      0.656 |        0.083 |         1 |        0.498 |           0.031 |
| ('pca_logreg', 'Control', 'Olaparib')            |   0.699 |        nan | 0.682 | 0.716 |   0.173 |  1.8   |      0.677 |        0.096 |         1 |        0.507 |           0.024 |
| ('pca_logreg', 'NK', 'Carboplatin')              |   0.703 |        nan | 0.683 | 0.722 |   0.165 |  2.012 |      0.673 |        0.082 |         1 |        0.497 |           0.03  |
| ('pca_logreg', 'NK', 'Control')                  |   0.692 |        nan | 0.666 | 0.715 |   0.251 |  1.699 |      0.687 |        0.148 |         1 |        0.526 |           0.031 |
| ('pca_logreg', 'NK', 'Olaparib')                 |   0.713 |        nan | 0.697 | 0.731 |   0.193 |  2.008 |      0.689 |        0.096 |         1 |        0.523 |           0.046 |
| ('pca_logreg', 'Olaparib', 'Carboplatin')        |   0.718 |        nan | 0.697 | 0.737 |   0.176 |  2.137 |      0.683 |        0.082 |         1 |        0.458 |           0.041 |
| ('pca_logreg', 'Olaparib', 'Control')            |   0.69  |        nan | 0.666 | 0.713 |   0.264 |  1.785 |      0.689 |        0.148 |         1 |        0.518 |           0.04  |
| ('pca_logreg', 'Olaparib', 'NK')                 |   0.673 |        nan | 0.655 | 0.691 |   0.155 |  1.856 |      0.663 |        0.083 |         1 |        0.509 |           0.037 |
| ('pca_logreg_pooled', 'Carboplatin', 'Control')  |   0.7   |        nan | 0.676 | 0.722 |   0.267 |  1.808 |      0.696 |        0.148 |         1 |        0.484 |           0.02  |
| ('pca_logreg_pooled', 'Carboplatin', 'NK')       |   0.679 |        nan | 0.662 | 0.697 |   0.154 |  1.849 |      0.67  |        0.083 |         1 |        0.499 |           0.012 |
| ('pca_logreg_pooled', 'Carboplatin', 'Olaparib') |   0.724 |        nan | 0.708 | 0.741 |   0.198 |  2.057 |      0.695 |        0.096 |         1 |        0.489 |           0.026 |
| ('pca_logreg_pooled', 'Control', 'Carboplatin')  |   0.72  |        nan | 0.702 | 0.739 |   0.177 |  2.152 |      0.688 |        0.082 |         1 |        0.496 |           0.022 |
| ('pca_logreg_pooled', 'Control', 'NK')           |   0.679 |        nan | 0.662 | 0.697 |   0.154 |  1.849 |      0.67  |        0.083 |         1 |        0.516 |           0.014 |
| ('pca_logreg_pooled', 'Control', 'Olaparib')     |   0.724 |        nan | 0.708 | 0.741 |   0.198 |  2.057 |      0.695 |        0.096 |         1 |        0.446 |           0.016 |
| ('pca_logreg_pooled', 'NK', 'Carboplatin')       |   0.72  |        nan | 0.702 | 0.739 |   0.177 |  2.152 |      0.688 |        0.082 |         1 |        0.522 |           0.026 |
| ('pca_logreg_pooled', 'NK', 'Control')           |   0.7   |        nan | 0.676 | 0.722 |   0.267 |  1.808 |      0.696 |        0.148 |         1 |        0.521 |           0.012 |
| ('pca_logreg_pooled', 'NK', 'Olaparib')          |   0.724 |        nan | 0.708 | 0.741 |   0.198 |  2.057 |      0.695 |        0.096 |         1 |        0.512 |           0.019 |
| ('pca_logreg_pooled', 'Olaparib', 'Carboplatin') |   0.72  |        nan | 0.702 | 0.739 |   0.177 |  2.152 |      0.688 |        0.082 |         1 |        0.519 |           0.016 |
| ('pca_logreg_pooled', 'Olaparib', 'Control')     |   0.7   |        nan | 0.676 | 0.722 |   0.267 |  1.808 |      0.696 |        0.148 |         1 |        0.477 |           0.021 |
| ('pca_logreg_pooled', 'Olaparib', 'NK')          |   0.679 |        nan | 0.662 | 0.697 |   0.154 |  1.849 |      0.67  |        0.083 |         1 |        0.533 |           0.008 |
| ('pca_logreg_tuned', 'Carboplatin', 'Control')   |   0.692 |        nan | 0.67  | 0.716 |   0.26  |  1.759 |      0.688 |        0.148 |         1 |        0.521 |         nan     |
| ('pca_logreg_tuned', 'Carboplatin', 'NK')        |   0.668 |        nan | 0.65  | 0.685 |   0.148 |  1.779 |      0.666 |        0.083 |         1 |        0.481 |         nan     |
| ('pca_logreg_tuned', 'Carboplatin', 'Olaparib')  |   0.717 |        nan | 0.699 | 0.737 |   0.195 |  2.025 |      0.684 |        0.096 |         1 |        0.554 |         nan     |
| ('pca_logreg_tuned', 'Control', 'Carboplatin')   |   0.702 |        nan | 0.684 | 0.721 |   0.157 |  1.91  |      0.681 |        0.082 |         1 |        0.496 |         nan     |
| ('pca_logreg_tuned', 'Control', 'NK')            |   0.663 |        nan | 0.644 | 0.682 |   0.135 |  1.614 |      0.655 |        0.083 |         1 |        0.47  |         nan     |
| ('pca_logreg_tuned', 'Control', 'Olaparib')      |   0.699 |        nan | 0.682 | 0.715 |   0.173 |  1.796 |      0.677 |        0.096 |         1 |        0.428 |         nan     |
| ('pca_logreg_tuned', 'NK', 'Carboplatin')        |   0.702 |        nan | 0.683 | 0.722 |   0.165 |  2.012 |      0.673 |        0.082 |         1 |        0.507 |         nan     |
| ('pca_logreg_tuned', 'NK', 'Control')            |   0.692 |        nan | 0.666 | 0.715 |   0.251 |  1.7   |      0.687 |        0.148 |         1 |        0.477 |         nan     |
| ('pca_logreg_tuned', 'NK', 'Olaparib')           |   0.713 |        nan | 0.697 | 0.731 |   0.193 |  2.006 |      0.689 |        0.096 |         1 |        0.512 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'Carboplatin')  |   0.718 |        nan | 0.696 | 0.736 |   0.177 |  2.15  |      0.682 |        0.082 |         1 |        0.508 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'Control')      |   0.688 |        nan | 0.664 | 0.711 |   0.264 |  1.787 |      0.688 |        0.148 |         1 |        0.469 |         nan     |
| ('pca_logreg_tuned', 'Olaparib', 'NK')           |   0.671 |        nan | 0.653 | 0.689 |   0.156 |  1.865 |      0.661 |        0.083 |         1 |        0.514 |         nan     |
| ('pca_smooth_logreg', 'Carboplatin', 'Control')  |   0.695 |        nan | 0.672 | 0.719 |   0.262 |  1.774 |      0.689 |        0.148 |         1 |        0.483 |           0.031 |
| ('pca_smooth_logreg', 'Carboplatin', 'NK')       |   0.673 |        nan | 0.654 | 0.69  |   0.15  |  1.794 |      0.667 |        0.083 |         1 |        0.511 |           0.027 |
| ('pca_smooth_logreg', 'Carboplatin', 'Olaparib') |   0.722 |        nan | 0.703 | 0.741 |   0.198 |  2.055 |      0.688 |        0.096 |         1 |        0.505 |           0.043 |
| ('pca_smooth_logreg', 'Control', 'Carboplatin')  |   0.707 |        nan | 0.69  | 0.727 |   0.164 |  1.993 |      0.687 |        0.082 |         1 |        0.493 |           0.048 |
| ('pca_smooth_logreg', 'Control', 'NK')           |   0.665 |        nan | 0.645 | 0.684 |   0.139 |  1.665 |      0.656 |        0.083 |         1 |        0.515 |           0.011 |
| ('pca_smooth_logreg', 'Control', 'Olaparib')     |   0.703 |        nan | 0.686 | 0.719 |   0.181 |  1.883 |      0.677 |        0.096 |         1 |        0.522 |           0.053 |
| ('pca_smooth_logreg', 'NK', 'Carboplatin')       |   0.712 |        nan | 0.693 | 0.732 |   0.175 |  2.126 |      0.681 |        0.082 |         1 |        0.498 |           0.035 |
| ('pca_smooth_logreg', 'NK', 'Control')           |   0.69  |        nan | 0.665 | 0.714 |   0.255 |  1.727 |      0.686 |        0.148 |         1 |        0.53  |           0.028 |
| ('pca_smooth_logreg', 'NK', 'Olaparib')          |   0.718 |        nan | 0.701 | 0.737 |   0.2   |  2.081 |      0.69  |        0.096 |         1 |        0.497 |           0.052 |
| ('pca_smooth_logreg', 'Olaparib', 'Carboplatin') |   0.724 |        nan | 0.701 | 0.743 |   0.182 |  2.22  |      0.687 |        0.082 |         1 |        0.511 |           0.03  |
| ('pca_smooth_logreg', 'Olaparib', 'Control')     |   0.69  |        nan | 0.665 | 0.713 |   0.266 |  1.803 |      0.688 |        0.148 |         1 |        0.498 |           0.041 |
| ('pca_smooth_logreg', 'Olaparib', 'NK')          |   0.676 |        nan | 0.658 | 0.694 |   0.156 |  1.872 |      0.663 |        0.083 |         1 |        0.505 |           0.027 |


## cross-arm matrix (pca_logreg)

| train       |   Carboplatin |   Olaparib |    NK |   Control |
|:------------|--------------:|-----------:|------:|----------:|
| Carboplatin |         0.723 |      0.717 | 0.669 |     0.694 |
| Olaparib    |         0.718 |      0.727 | 0.673 |     0.69  |
| NK          |         0.703 |      0.713 | 0.68  |     0.692 |
| Control     |         0.703 |      0.699 | 0.664 |     0.704 |


## fitness confound

| drug_arm    |   n_drug |   prev_drug |   n_control |   prev_control |   auroc_drug_model_on_drug |   auroc_fitness_model_on_drug |   auroc_control_model_on_control |   auroc_drug_model_on_control |   specificity_index |   auroc_drug_model_size_matched |   auroc_fitness_model_same_cells |   specificity_index_size_matched |   auroc_drug_residual_on_drug |   auroc_drug_within_fitness_quintiles |   corr_drug_vs_fitness_score |   lrt_stat |   lrt_p | features   | cc_mode     |
|:------------|---------:|------------:|------------:|---------------:|---------------------------:|------------------------------:|---------------------------------:|------------------------------:|--------------------:|--------------------------------:|---------------------------------:|---------------------------------:|------------------------------:|--------------------------------------:|-----------------------------:|-----------:|--------:|:-----------|:------------|
| Carboplatin |     8942 |      0.0822 |        4183 |         0.1477 |                     0.7235 |                        0.7026 |                           0.7042 |                        0.6936 |              0.0209 |                          0.7108 |                           0.6988 |                           0.0119 |                        0.6207 |                                0.621  |                       0.7963 |    98.1709 |       0 | pca        | regress_all |
| Olaparib    |     9394 |      0.0962 |        4183 |         0.1477 |                     0.727  |                        0.6991 |                           0.7042 |                        0.6901 |              0.0279 |                          0.7237 |                           0.6977 |                           0.026  |                        0.6289 |                                0.6357 |                       0.7893 |   137.789  |       0 | pca        | regress_all |
| NK          |    10123 |      0.0835 |        4183 |         0.1477 |                     0.6803 |                        0.6639 |                           0.7042 |                        0.6917 |              0.0164 |                          0.6679 |                           0.6651 |                           0.0027 |                        0.5826 |                                0.6049 |                       0.7811 |    71.5346 |       0 | pca        | regress_all |


## ceiling decomposition (pi=0.1)

| model            | arm         |   pi |   auroc_oof |   rho_obs |   rho_fate | saturated   |   auroc_if_sister_seen |   sister_cost |
|:-----------------|:------------|-----:|------------:|----------:|-----------:|:------------|-----------------------:|--------------:|
| mlp              | Carboplatin |  0.1 |       0.723 |     0.447 |      0.649 | False       |                  0.818 |         0.095 |
| mlp              | Control     |  0.1 |       0.697 |     0.427 |      0.52  | False       |                  0.74  |         0.043 |
| mlp              | NK          |  0.1 |       0.685 |     0.37  |      0.557 | False       |                  0.775 |         0.09  |
| mlp              | Olaparib    |  0.1 |       0.722 |     0.454 |      0.621 | False       |                  0.801 |         0.079 |
| pca_logreg_tuned | Carboplatin |  0.1 |       0.72  |     0.441 |      0.578 | False       |                  0.786 |         0.065 |
| pca_logreg_tuned | Control     |  0.1 |       0.704 |     0.442 |      0.524 | False       |                  0.742 |         0.038 |
| pca_logreg_tuned | NK          |  0.1 |       0.672 |     0.344 |      0.531 | False       |                  0.763 |         0.091 |
| pca_logreg_tuned | Olaparib    |  0.1 |       0.727 |     0.464 |      0.652 | False       |                  0.814 |         0.088 |
| persist_gnn      | Carboplatin |  0.1 |       0.721 |     0.442 |      0.573 | False       |                  0.783 |         0.063 |
| persist_gnn      | Control     |  0.1 |       0.689 |     0.41  |      0.468 | False       |                  0.716 |         0.027 |
| persist_gnn      | NK          |  0.1 |       0.664 |     0.327 |      0.434 | False       |                  0.717 |         0.053 |
| persist_gnn      | Olaparib    |  0.1 |       0.716 |     0.442 |      0.57  | False       |                  0.777 |         0.061 |


## ceiling_regress_all.csv

| arm         |   prevalence |   rho |   pi |   auroc_ceiling | cc_mode     |
|:------------|-------------:|------:|-----:|----------------:|:------------|
| Carboplatin |        0.082 |  0.92 |  0   |           0.973 | regress_all |
| Carboplatin |        0.082 |  0.92 |  0.1 |           0.925 | regress_all |
| Carboplatin |        0.082 |  0.92 |  0.2 |           0.878 | regress_all |
| Olaparib    |        0.096 |  0.92 |  0   |           0.971 | regress_all |
| Olaparib    |        0.096 |  0.92 |  0.1 |           0.924 | regress_all |
| Olaparib    |        0.096 |  0.92 |  0.2 |           0.877 | regress_all |
| NK          |        0.083 |  0.92 |  0   |           0.972 | regress_all |
| NK          |        0.083 |  0.92 |  0.1 |           0.925 | regress_all |
| NK          |        0.083 |  0.92 |  0.2 |           0.878 | regress_all |
| Control     |        0.148 |  0.92 |  0   |           0.964 | regress_all |
| Control     |        0.148 |  0.92 |  0.1 |           0.918 | regress_all |
| Control     |        0.148 |  0.92 |  0.2 |           0.872 | regress_all |


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
