# Iteration summary

The validation rule nominates **static_timeout_60_reset** for future paper evaluation. It improves validation return by 1.43% and Sharpe by 0.588.

5/10 improve validation return and Sharpe; 5/10 improve the previously viewed test; 3 improve both periods. 0 paired comparisons meet the full stage-adjusted evidence rule. All historical results are exploratory.

| strategy                     | stage      |   return |   sharpe |   delta_return |   delta_sharpe |   max_drawdown |   capital_utilization |   risk_scaled_control_return |   completed_trades |   timeouts |
|:-----------------------------|:-----------|---------:|---------:|---------------:|---------------:|---------------:|----------------------:|-----------------------------:|-------------------:|-----------:|
| rolling_mean_126             | validation |   0.0089 |   0.3807 |        -0.0241 |        -0.3528 |        -0.0118 |                0.0880 |                       0.0177 |                  5 |          0 |
| rolling_mean_126             | test       |   0.0112 |   0.4353 |        -0.0034 |         0.1430 |        -0.0191 |                0.1080 |                       0.0052 |                  7 |          0 |
| rolling_mean_252             | validation |   0.0269 |   0.5523 |        -0.0062 |        -0.1813 |        -0.0331 |                0.2135 |                       0.0253 |                 10 |          0 |
| rolling_mean_252             | test       |   0.0156 |   0.3900 |         0.0011 |         0.0977 |        -0.0191 |                0.2311 |                       0.0124 |                  9 |          0 |
| static_local_beta_entry      | validation |  -0.0060 |  -0.0746 |         0.0003 |         0.0002 |        -0.0403 |                0.7034 |                      -0.0060 |                  4 |          0 |
| static_local_beta_entry      | test       |   0.0206 |   0.2680 |         0.0024 |         0.0310 |        -0.0656 |                0.6927 |                       0.0176 |                  8 |          0 |
| static_local_beta_reduction  | validation |  -0.0085 |  -0.1202 |        -0.0022 |        -0.0454 |        -0.0391 |                0.6731 |                      -0.0058 |                  4 |          0 |
| static_local_beta_reduction  | test       |   0.0083 |   0.1288 |        -0.0099 |        -0.1082 |        -0.0685 |                0.6218 |                       0.0169 |                  8 |          0 |
| rolling_local_beta_entry     | validation |   0.0354 |   0.8404 |         0.0024 |         0.1068 |        -0.0244 |                0.2178 |                       0.0307 |                  7 |          0 |
| rolling_local_beta_entry     | test       |   0.0164 |   0.3272 |         0.0018 |         0.0348 |        -0.0351 |                0.4193 |                       0.0126 |                  6 |          0 |
| rolling_local_beta_reduction | validation |   0.0342 |   0.8410 |         0.0011 |         0.1075 |        -0.0231 |                0.2228 |                       0.0308 |                  7 |          0 |
| rolling_local_beta_reduction | test       |   0.0102 |   0.2206 |        -0.0044 |        -0.0717 |        -0.0348 |                0.3879 |                       0.0129 |                  6 |          0 |
| static_timeout_60_reset      | validation |   0.0080 |   0.5135 |         0.0143 |         0.5883 |        -0.0093 |                0.0741 |                      -0.0024 |                  4 |          4 |
| static_timeout_60_reset      | test       |   0.0178 |   0.8878 |        -0.0003 |         0.6509 |        -0.0105 |                0.0882 |                       0.0020 |                  8 |          4 |
| static_timeout_120_reset     | validation |   0.0003 |   0.0175 |         0.0066 |         0.0923 |        -0.0143 |                0.1332 |                      -0.0032 |                  6 |          6 |
| static_timeout_120_reset     | test       |   0.0319 |   1.3486 |         0.0137 |         1.1116 |        -0.0105 |                0.1271 |                       0.0035 |                  7 |          2 |
| rolling_timeout_60_reset     | validation |   0.0164 |   1.1441 |        -0.0167 |         0.4106 |        -0.0078 |                0.0606 |                       0.0148 |                  6 |          4 |
| rolling_timeout_60_reset     | test       |   0.0174 |   0.6807 |         0.0029 |         0.3884 |        -0.0104 |                0.0848 |                       0.0036 |                  7 |          6 |
| rolling_timeout_120_reset    | validation |   0.0013 |   0.0626 |        -0.0317 |        -0.6710 |        -0.0145 |                0.1067 |                       0.0182 |                  8 |          5 |
| rolling_timeout_120_reset    | test       |   0.0086 |   0.3046 |        -0.0059 |         0.0123 |        -0.0129 |                0.1554 |                       0.0063 |                  6 |          4 |

[Full analysis](report.md)
