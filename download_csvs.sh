{
  year=$(date +%Y)

  wget https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_mythenquai_$year.csv
  wget https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_tiefenbrunnen_$year.csv

  mv -f messwerte_mythenquai_$year.csv ./csv/messwerte_mythenquai.csv
  mv -f messwerte_tiefenbrunnen_$year.csv ./csv/messwerte_tiefenbrunnen.csv
} || {
    echo "Download of CSV files failed. Relying on fallback data."
}