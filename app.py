import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Tuple


# --- Configuração da página ---
# Define o título da página, o ícone e o layout para ocupar a largura inteira
st.set_page_config(
    page_title="Dashboard de salários da área de dados",
    page_icon="📊",
    layout="wide",
)


# --- Carregamento de dados com validação e cache ---
@st.cache_data
def carregar_dados() -> pd.DataFrame:
    try:
        return pd.read_csv("Dados.csv")
    except Exception as e:
        st.error(f"Erro ao carregar Dados.csv: {e}")
        return pd.DataFrame()


df = carregar_dados()


# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

anos_disponiveis = sorted(df["ano"].unique()) if not df.empty else []
anos_selecionados = st.sidebar.multiselect(
    "Ano",
    anos_disponiveis,
    default=anos_disponiveis,
    help="Selecione um ou mais anos para análise.",
)

senioridades_disponiveis = sorted(df["senioridade"].unique()) if not df.empty else []
senioridades_selecionadas = st.sidebar.multiselect(
    "Senioridade",
    senioridades_disponiveis,
    default=senioridades_disponiveis,
    help="Filtre por nível de senioridade do profissional.",
)

contratos_disponiveis = sorted(df["contrato"].unique()) if not df.empty else []
contratos_selecionados = st.sidebar.multiselect(
    "Tipo de Contrato",
    contratos_disponiveis,
    default=contratos_disponiveis,
    help="Filtre por tipo de vínculo empregatício.",
)

tamanhos_disponiveis = sorted(df["tamanho_empresa"].unique()) if not df.empty else []
tamanhos_selecionados = st.sidebar.multiselect(
    "Tamanho da Empresa",
    tamanhos_disponiveis,
    default=tamanhos_disponiveis,
    help="Filtre pelo porte da empresa.",
)


# --- Função de filtragem ---
def filtrar_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df[
        (df["ano"].isin(anos_selecionados))
        & (df["senioridade"].isin(senioridades_selecionadas))
        & (df["contrato"].isin(contratos_selecionados))
        & (df["tamanho_empresa"].isin(tamanhos_selecionados))
    ]


df_filtrado = filtrar_df(df)

# --- Conteúdo Principal ---
st.title("🎲 Dashboard de Análise de Salários na Área de Dados")
st.markdown(
    "Explore os dados salariais na área de dados nos últimos anos. Utilize os filtros à esquerda para refinar sua análise."
)


# --- Métricas Principais (KPIs) ---
st.subheader("Métricas gerais (Salário anual em USD)")

if not df_filtrado.empty:
    salario_medio = df_filtrado["usd"].mean()
    salario_mediano = df_filtrado["usd"].median()
    salario_maximo = df_filtrado["usd"].max()
    total_registros = df_filtrado.shape[0]
    cargo_mais_frequente = df_filtrado["cargo"].mode()[0]
else:
    (
        salario_medio,
        salario_mediano,
        salario_maximo,
        total_registros,
        cargo_mais_frequente,
    ) = (0, 0, 0, 0, "")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Salário médio", f"${salario_medio:,.0f}")
col2.metric("Salário mediano", f"${salario_mediano:,.0f}")
col3.metric("Salário máximo", f"${salario_maximo:,.0f}")
col4.metric("Total de registros", f"{total_registros:,}")
col5.metric("Cargo mais frequente", cargo_mais_frequente)

st.markdown("---")

# --- Análises Visuais com Plotly ---
st.subheader("Gráficos")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_filtrado.empty:
        top_cargos = (
            df_filtrado.groupby("cargo")["usd"]
            .mean()
            .nlargest(10)
            .sort_values(ascending=True)
            .reset_index()
        )
        grafico_cargos = px.bar(
            top_cargos,
            x="usd",
            y="cargo",
            orientation="h",
            title="Top 10 cargos por salário médio",
            labels={"usd": "Média salarial anual (USD)", "cargo": ""},
        )
        grafico_cargos.update_layout(
            title_x=0.1, yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(grafico_cargos, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de cargos.")

with col_graf2:
    if not df_filtrado.empty:
        grafico_hist = px.histogram(
            df_filtrado,
            x="usd",
            nbins=30,
            title="Distribuição de salários anuais",
            labels={"usd": "Faixa salarial (USD)", "count": ""},
        )
        grafico_hist.update_layout(title_x=0.1)
        st.plotly_chart(grafico_hist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de distribuição.")

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    if not df_filtrado.empty:
        remoto_contagem = df_filtrado["remoto"].value_counts().reset_index()
        remoto_contagem.columns = ["tipo_trabalho", "quantidade"]
        grafico_remoto = px.pie(
            remoto_contagem,
            names="tipo_trabalho",
            values="quantidade",
            title="Proporção dos tipos de trabalho",
            hole=0.5,
        )
        grafico_remoto.update_traces(textinfo="percent+label")
        grafico_remoto.update_layout(title_x=0.1)
        st.plotly_chart(grafico_remoto, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico dos tipos de trabalho.")

with col_graf4:
    if not df_filtrado.empty:
        df_ds = df_filtrado[df_filtrado["cargo"] == "Data Scientist"]
        media_ds_pais = df_ds.groupby("residencia_iso3")["usd"].mean().reset_index()
        grafico_paises = px.choropleth(
            media_ds_pais,
            locations="residencia_iso3",
            color="usd",
            color_continuous_scale=px.colors.sequential.Viridis,
            title="Salário médio de Cientista de Dados por país",
            labels={"usd": "Salário médio (USD)", "residencia_iso3": "País"},
            hover_data={"residencia_iso3": True, "usd": ":.0f"},
        )
        grafico_paises.update_layout(
            title_x=0.5,
            geo=dict(showframe=False, showcoastlines=True),
            coloraxis_colorbar=dict(
                title="USD",
                tickformat=",",
                len=1,
                thickness=15,
                tickvals=[
                    int(media_ds_pais["usd"].min()),
                    int((media_ds_pais["usd"].min() + media_ds_pais["usd"].max()) / 2),
                    int(media_ds_pais["usd"].max()),
                ],
                ticktext=[
                    f"${int(media_ds_pais['usd'].min()):,}",
                    f"${int((media_ds_pais['usd'].min() + media_ds_pais['usd'].max())/2):,}",
                    f"${int(media_ds_pais['usd'].max()):,}",
                ],
            ),
        )
        grafico_paises.update_traces(
            hovertemplate="<b>País:</b> %{location}<br>Salário médio: $%{z:,.0f}<extra></extra>"
        )
        st.plotly_chart(grafico_paises, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de países.")

# --- Tabela de Dados Detalhados ---
with st.expander("🔎 Ver tabela de dados detalhados", expanded=False):
    st.dataframe(df_filtrado, use_container_width=True)
