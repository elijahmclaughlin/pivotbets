# Pivot Bets Streamlit App
This is a Streamlit web application that displays sports betting predictions and analytics for the NFL and College Football. The app fetches live data from a Supabase backend to show game predictions, player props, and model performance.

## Features
- **League Selection:** View predictions for NFL, College Football, and NFL Player Props.
- **Model Accuracy:** Displays the historical accuracy of the prediction models for Moneyline, Spread (ATS), and Totals (O/U).
- **Game Predictions:** Shows predicted winners, scores, and probabilities for upcoming matchups.
- **Player Props:** (NFL) Displays player-specific projections for yards, TDs, and boom/bust probabilities.
- **Dynamic Filtering:** Users can filter predictions by specific matchups

## Tech Stack
- **Frontend:** Streamlit
- **Backend:** models built in R, daily runs through GitHub, hosted in Supabase
- **Languages:** R, Python, SQL
- **Core Libraries:** pandas, supabase-client, tidyverse, cluster (k-means)
- **Custom Models:** Bayesian Inference simulation, Monte Carlo integration

