{
  year=$(date +%Y)

  echo "Downloading CSVs for $year"
  wget https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_mythenquai_$year.csv
  wget https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_tiefenbrunnen_$year.csv
  echo "Done"

  mv -f messwerte_mythenquai_$year.csv ./csv/messwerte_mythenquai.csv
  mv -f messwerte_tiefenbrunnen_$year.csv ./csv/messwerte_tiefenbrunnen.csv
  echo "Moved CSVs to ./csv"
} || {
    echo "Download of CSV files failed. Relying on fallback data."
}