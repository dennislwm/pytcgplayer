# pytcgplayer

<h1 align="center" style="border-bottom: none;">pytcgplayer</h1>
<h3 align="center">Python CLI application for processing TCGPlayer trading card price data with time series alignment and technical analysis.</h3>
<br />
<p align="center">
  <p align="center">
    <a href="https://github.com/dennislwm/pytcgplayer/issues/new?template=bug_report.yml">Bug report</a>
    ·
    <a href="https://github.com/dennislwm/pytcgplayer/issues/new?template=feature_request.yml">Feature request</a>
    ·
    <a href="https://github.com/dennislwm/pytcgplayer/wiki">Read Docs</a>
  </p>
</p>
<br />

---

![GitHub repo size](https://img.shields.io/github/repo-size/dennislwm/pytcgplayer?style=plastic)
![GitHub language count](https://img.shields.io/github/languages/count/dennislwm/pytcgplayer?style=plastic)
![GitHub top language](https://img.shields.io/github/languages/top/dennislwm/pytcgplayer?style=plastic)
![GitHub last commit](https://img.shields.io/github/last-commit/dennislwm/pytcgplayer?color=red&style=plastic)
![Visitors count](https://hits.sh/github.com/dennislwm/pytcgplayer/hits.svg)
![GitHub stars](https://img.shields.io/github/stars/dennislwm/pytcgplayer?style=social)
![GitHub forks](https://img.shields.io/github/forks/dennislwm/pytcgplayer?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/dennislwm/pytcgplayer?style=social)
![GitHub followers](https://img.shields.io/github/followers/dennislwm?style=social)

## Overview 📊

**pytcgplayer** is a Python CLI application that processes TCGPlayer trading card price data, featuring advanced time series alignment and technical analysis capabilities. The application reads TCGPlayer URLs from CSV files, fetches price history data, parses markdown price tables, and outputs normalized price data in schema v2.0 format for efficient analysis and charting.

### Key Features

- **🔄 Time Series Alignment**: Intelligent alignment system with 100% signature coverage
- **📈 Technical Analysis**: DBS (Defensive Bull/Bear Signal) analysis with automated alerts
- **🛠️ Interactive Workbench**: Guided discovery process for optimal filter configurations
- **📊 Multiple Chart Types**: CSV time series data and yfinance stock comparison
- **⚡ Schema Management**: Automated v1.0 to v2.0 format conversion with numeric types
- **🔍 Rate Limiting**: Built-in exponential backoff for API reliability

## Getting Started 🚀

### Quick Start
```bash
make pipenv_new && make install_deps  # Setup environment
make sample && make run_verbose       # Create test data and run
make test                             # Run all tests
make convert_schema                   # Convert v1.0 to v2.0 format
```

### Sample Usage
```bash
# Input CSV format (TCGPlayer URLs only)
set,type,period,name,url
SV08.5,Card,3M,Umbreon ex 161,https://r.jina.ai/https://www.tcgplayer.com/product/610516/...

# Command execution
$ PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv --verbose

# Output CSV format (Schema v2.0 - Normalized price history)
set,type,period,name,period_start_date,period_end_date,timestamp,holofoil_price,volume
SV08.5,Card,3M,Umbreon ex 161,2025-04-20,2025-04-22,2025-07-24 15:00:00,1451.66,0
```

### Interactive Workbench Commands
```bash
make workbench_discover  # Find optimal configurations
make workbench_analyze   # Analyze specific filters
make workbench_save      # Save configurations
make workbench_list      # List saved configs
make workbench_run       # Execute saved config
```

### Technical Analysis Charts
```bash
make chart           # Compare CSV time series data
make chart_yfinance  # Compare stock data (XLU vs VTI)
make chart_help      # Show chart options
```

We have a thorough guide on how to set up and get started with `pytcgplayer` in our [documentation](https://github.com/dennislwm/pytcgplayer/wiki).

## Bugs or Requests 🐛

If you encounter any problems feel free to open an [issue](https://github.com/dennislwm/pytcgplayer/issues/new?template=bug_report.yml). If you feel the project is missing a feature, please raise a [ticket](https://github.com/dennislwm/pytcgplayer/issues/new?template=feature_request.yml) on GitHub and I'll look into it. Pull requests are also welcome.

## 📫 How to reach me
<p>
<a href="https://www.linkedin.com/in/dennislwm"><img src="https://img.shields.io/badge/LinkedIn-blue?style=for-the-badge&logo=linkedin&labelColor=blue" height=25></a>
<a href="https://twitter.com/hypowork"><img src="https://img.shields.io/badge/twitter-%231DA1F2.svg?&style=for-the-badge&logo=twitter&logoColor=white" height=25></a>
<a href="https://leetradetitan.medium.com"><img src="https://img.shields.io/badge/medium-%2312100E.svg?&style=for-the-badge&logo=medium&logoColor=white" height=25></a>
<a href="https://dev.to/dennislwm"><img src="https://img.shields.io/badge/DEV.TO-%230A0A0A.svg?&style=for-the-badge&logo=dev-dot-to&logoColor=white" height=25></a>
<a href="https://www.youtube.com/user/dennisleewm"><img src="https://img.shields.io/badge/-YouTube-red?&style=for-the-badge&logo=youtube&logoColor=white" height=25></a>
</p>
<p>
<span class="badge-buymeacoffee"><a href="https://ko-fi.com/dennislwm" title="Donate to this project using Buy Me A Coffee"><img src="https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg" alt="Buy Me A Coffee donate button" /></a></span>
<span class="badge-patreon"><a href="https://patreon.com/dennislwm" title="Donate to this project using Patreon"><img src="https://img.shields.io/badge/patreon-donate-yellow.svg" alt="Patreon donate button" /></a></span>
<span class="badge-newsletter"><a href="https://buttondown.email/dennislwm" title="Subscribe to Newsletter"><img src="https://img.shields.io/badge/newsletter-subscribe-blue.svg" alt="Subscribe Dennis Lee's Newsletter" /></a></span>