import pandas as pd
import matplotlib.pyplot as plt

# Lembrando que esse é o grafico de preço do Portal 2

# Carrega o arquivo CSV
file_name = "price_history.csv"
df = pd.read_csv(file_name)

# Prepara os dados
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
steam_df = df[df["shop_id"] == 61].copy()
steam_df = steam_df.sort_values(by="timestamp")

# Edite as datas para filtrar o período
start_date = "2020-05-06"
end_date = "2025-03-02"

start_date = pd.to_datetime(start_date, utc=True)
end_date = pd.to_datetime(end_date, utc=True)

# Aplica o filtro
filtered_df = steam_df[
    (steam_df["timestamp"] >= start_date) & (steam_df["timestamp"] <= end_date)
].copy()


# Cria o gráfico
plt.style.use("dark_background")
plt.figure(figsize=(30, 7))
plt.step(
    filtered_df["timestamp"],
    filtered_df["price_amount"],
    where="post",
    color="lime",
    linewidth=2,
)

plt.fill_between(
    filtered_df["timestamp"],
    filtered_df["price_amount"],
    step="post",
    alpha=0.2,
    color="cyan",
)

plt.axhline(y=50, color="skyblue", linestyle="--", alpha=0.6)


plt.title(f"Steam Price from {start_date} to {end_date}", fontsize=16)
plt.xlabel("Date", fontsize=12)
plt.ylabel(f"Price ({filtered_df['price_currency'].iloc[0]})", fontsize=12)

plt.ylim(bottom=0)
plt.gcf().autofmt_xdate()


# Exibe o gráfico final
plt.tight_layout()
plt.show()
