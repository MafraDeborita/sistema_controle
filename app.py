import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import pandas as pd
from datetime import datetime


# Configuração da página DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT
st.set_page_config(
    page_title="Dashboard de Compras e Serviços", 
    layout="wide",
    page_icon="icon/tendencia.png"
)

st.markdown(""" ⚠️ Aviso Importante

Este projeto utiliza dados públicos disponibilizados por órgão governamental, conforme previsto em lei de transparência.
Não há tratamento de dados pessoais em desacordo com a LGPD.
A finalidade é acadêmica e de estudo, sem uso comercial. """)


# Logo no topo centralizado
# Caminho absoluto para garantir que o arquivo seja encontrado
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "icon", "image.png")

# Linha de topo com a logo à direita
# top = st.columns([1, 1, 1])  # ajuste a proporção conforme desejar
# with top[2]:  # coluna da direita
st.image(logo_path, width=300)  # ajuste o tamanho

# Adicionar utils ao path de forma mais robusta
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_path = os.path.join(current_dir, 'utils')
sys.path.insert(0, utils_path)

# Tente importar de diferentes formas SEM USAR STREAMLIT DENTRO DO TRY
try:
    # Tentativa 1: Importação direta
    from data_loaders import load_excel_data, aplicar_filtros, get_diretorias_from_data
    import_success = True
except ImportError:
    try:
        # Tentativa 2: Importar o módulo completo
        import data_loaders
        load_excel_data = data_loaders.load_excel_data
        aplicar_filtros = data_loaders.aplicar_filtros
        get_diretorias_from_data = data_loaders.get_diretorias_from_data
        import_success = True
    except ImportError:
        import_success = False
        
        # Definir funções locais como fallback
        def load_excel_data(file_path):
            """Carrega dados do arquivo Excel"""
            try:
                data = {}
                # Mapeamento das abas (do seu data_loaders.py)
                sheets = {
                    'orcamento_geral': 'ORCAMENTO_GERAL',
                    'planejamento_aquisicoes': 'PLANEJAMENTO_AQUISICOES',                    
                    'ordens_de_compra': 'ORDENS_DE_COMPRA',
                    'nf_de_servico': 'NF_DE_SERVICO',
                    'nf_de_aquisicao': 'NF_DE_AQUISICAO',
                    'aquisicao_mensal': 'AQUISICAO_MENSAL',
                    'servico_mensal': 'SERVICO_MENSAL',
                    'proposta_orcamentaria': 'PROPOSTA_ORCAMENTARIA',
                    'nao_planejado': 'NAO_PLANEJADO'
                }
                
                for key, sheet_name in sheets.items():
                    try:
                        data[key] = pd.read_excel(file_path, sheet_name=sheet_name)
                    except Exception:
                        data[key] = pd.DataFrame()
                
                return data
            except Exception as e:
                return {}
        
        def aplicar_filtros(df, coluna_diretoria, diretorias_selecionadas):
            """Aplica filtros por diretoria"""
            if df.empty:
                return df
            if coluna_diretoria not in df.columns:
                return df
            return df[df[coluna_diretoria].isin(diretorias_selecionadas)]
        
        def get_diretorias_from_data(data):
            """Extrai a lista de diretorias disponíveis nos dados"""
            diretorias = ['PR', 'DE', 'DG', 'DO', 'DC']
            
            if not data['orcamento_geral'].empty and 'diretoria' in data['orcamento_geral'].columns:
                diretorias_reais = data['orcamento_geral']['diretoria'].unique().tolist()
                if diretorias_reais:
                    return diretorias_reais
            
            return diretorias

# Agora podemos usar Streamlit normalmente
st.title("📊 Plano Anual de Contratações 2025")
st.markdown("Análise do comportamento de gastos por diretoria")

# Mostrar status da importação na sidebar
st.sidebar.header("Configurações")
if import_success:
    st.sidebar.success("✅ Módulo data_loaders importado com sucesso")
else:
    st.sidebar.warning("⚠️ Usando funções locais como fallback")

# Carregar dados - CORRIGIDO para pasta 'data/'
file_path = os.path.join("data", "controle_compras_servicos.xlsx")

# Verificar se o arquivo existe
if not os.path.exists(file_path):
    st.error(f"❌ Arquivo não encontrado: {file_path}")
    st.info(f"Por favor, coloque o arquivo 'controle_compras_servicos.xlsx' na pasta 'data/'")
    st.stop()

with st.spinner('Carregando dados do Excel...'):
    data = load_excel_data(file_path)

# Verificar se os dados principais foram carregados
if not data or all(df.empty for df in data.values()):
    st.error("""
    ❌ Não foi possível carregar os dados do Excel. 
    
    Verifique se:
    - O arquivo `controle_compras_servicos.xlsx` está na pasta 'data'
    - O arquivo não está corrompido
    - As abas têm os nomes corretos
    """)
    
    # Mostrar estrutura das abas carregadas
    st.subheader("Abas carregadas:")
    for key, df in data.items():
        st.write(f"- {key}: {len(df)} linhas")
    
    st.stop()

# Filtro por diretoria
diretorias = get_diretorias_from_data(data)
diretoria_selecionada = st.sidebar.multiselect(
    "Selecione a(s) diretoria(s):",
    options=diretorias,
    default=diretorias
)

# Layout do dashboard
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Visão Geral", "📦 Aquisições", "🛠️ Serviços", "📈 Análise Detalhada"])

#----------------------------------------------------------------------
#-----------------------------ABA 1---------------------------------------
with tab1:
    st.header("Visão Geral dos Orçamentos")
    
    if data['orcamento_geral'].empty:
        st.warning("📝 Dados de orçamento geral não disponíveis")
    else:
        orc_geral_filtrado = aplicar_filtros(data['orcamento_geral'], 'diretoria', diretoria_selecionada)
        
        # KPIs no topo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_planejado = orc_geral_filtrado['orcamento_planejado'].sum()
            st.metric("Orçamento Planejado", f"R$ {total_planejado:,.2f}")
        
        with col2:
            total_aprovado = orc_geral_filtrado['orcamento_aprovado'].sum()
            st.metric("Orçamento Aprovado", f"R$ {total_aprovado:,.2f}")
        
        with col3:
            total_fora_plano = orc_geral_filtrado['fora_do_plano'].sum()
            st.metric("Fora do Plano", f"R$ {total_fora_plano:,.2f}")
        
        with col4:
            if data['proposta_orcamentaria'].empty:
                meta_caema = total_aprovado * 1.1
            else:
                meta_caema = data['proposta_orcamentaria']['VALOR'].iloc[0]
            st.metric("Meta CAEMA", f"R$ {meta_caema:,.2f}")
        
        st.markdown("---")
        
        # ================================================
        # 📊 GRÁFICO 1 – Orçamento Planejado x Aprovado + Fora do Plano
    # ================================================
    st.subheader("📈 Gráfico 1: Orçamento Planejado vs Aprovado com Fora do Plano")
    #st.markdown("""
    #**Este gráfico mostra:**
    #- Orçamento Planejado (barras azuis claro)
    #- Orçamento Aprovado (barras azuis escuro)
    #- Fora do Plano (linha vermelha)

    #""")

    # ------------------------------------------------
    # FUNÇÃO DO GRÁFICO
    # ------------------------------------------------
    def grafico_orcamento_geral(df):


        def abreviar_valor(v):
            if v >= 1_000_000_000:
                return f"{v/1_000_000_000:.1f}B"
            elif v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            elif v >= 1_000:
                return f"{v/1_000:.1f}K"
            else:
                return f"{v:.0f}"


        fig = go.Figure()

        # --- BARRA 1: Orçamento Aprovado ---
        # Barras agrupadas
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['orcamento_aprovado'],
            name='Orçamento Aprovado',
            marker_color="#1341BE",
            text=[f"R${abreviar_valor(v)}" for v in df['orcamento_aprovado']],  # <-- VALORES AQUI
            textposition='outside',                                   # <-- APARECE EM CIMA
            textfont=dict(color='white', size=12)
        ))


        # --- BARRA 2: Orçamento Planejado ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['orcamento_planejado'],
            name='Orçamento Planejado',
            marker_color='#79A9FF',
            text=[f"R${abreviar_valor(v)}" for v in df['orcamento_planejado']],  # <-- VALORES AQUI
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))

        # Linha sobreposta suave
        fig.add_trace(go.Scatter(
            x=df['diretoria'],
            y=df['fora_do_plano'],
            name='Fora do Plano',
            mode='lines+markers+text',
            line=dict(width=3, color='red', shape='spline'),  # linha curva
            marker=dict(size=10, color='#003B73'),
            text=[f"R${abreviar_valor(v)}" for v in df['fora_do_plano']],
            textposition="top center",
            textfont=dict(color='#FFFFFF', size=12)
        ))

        # Layout geral
        fig.update_layout(
            title="Orçamento Geral por Diretoria",
            xaxis_title="Diretoria",
            yaxis_title="Valores (R$)",
            barmode='group',
            template="plotly_dark",
            legend_title="Legenda",
            height=600 
        )

        # --------- FORMATAÇÃO DOS NÚMEROS (R$ E ESCALA REDUZIDA) ---------
        fig.update_yaxes(
            tickprefix="R$",
            separatethousands=True,
            tickformat=".2s"  # 15M, 1.2M, 200K...
        )

        return fig


    # ------------------------------------------------
    # CONTAINER DO GRÁFICO
    # ------------------------------------------------
    with st.container():
        fig = grafico_orcamento_geral(orc_geral_filtrado)
        st.plotly_chart(fig, use_container_width=True)

        #acredito que Taliane não vai querer essa tabea aqui então vou deixala comentada por hora
        # Dados usados no gráfico
        #st.caption("📄 **Dados utilizados para o gráfico:**")
        #st.dataframe(
           # orc_geral_filtrado[['diretoria', 'orcamento_planejado', 'orcamento_aprovado', 'fora_do_plano']],
            #use_container_width=True
        #)

        st.markdown("---")

            
        #------------- ESPAÇO PARA GRÁFICO 2 ----------------------------------
        #------------- ESPAÇO PARA GRÁFICO 2 ----------------------------------
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📊 Gráfico 2: Plano Anual vs Meta CAEMA Geral")
            import plotly.graph_objects as go

            # -----------------------------------------
            #   CARREGAR OS VALORES DA PLANILHA
            # -----------------------------------------
            df_prop = data['proposta_orcamentaria']

            # Garantir que vírgulas virem ponto
            df_prop['VALOR'] = (
                df_prop['VALOR']
                .astype(str)
                .str.replace('.', '')
                .str.replace(',', '.')
                .astype(float)
            )

            # Pegar os valores pela descrição
            total_orcamento = df_prop.loc[df_prop['ORCAMENTO'] == 'GERAL CAEMA', 'VALOR'].values[0]
            plano_anual = df_prop.loc[df_prop['ORCAMENTO'] == 'PLANO ANUAL', 'VALOR'].values[0]

            # Percentual consumido
            perc = plano_anual / total_orcamento * 100

            # -----------------------------------------
            #   GRÁFICO DE PIZZA
            # -----------------------------------------
            fig_pizza = go.Figure(data=[
                go.Pie(
                    labels=['Plano Anual', 'Saldo do Orçamento'],
                    values=[plano_anual, total_orcamento],
                    hole=0.4,
                    hoverinfo="label+percent+value",
                    textinfo="label+percent",
                    texttemplate="%{label}<br>%{percent}<br>R$ %{value:,.0f}",
                    marker=dict(colors=["#75A4D4", "#1717AC"])
                )
            ])

            fig_pizza.update_layout(
                title="Percentual Consumido do Orçamento Geral",
                height=400,
                showlegend=True
            )

            st.plotly_chart(fig_pizza, use_container_width=True)

        with col_right:
            st.subheader("📊 Gráfico 2.1: Comparação Valor Absoluto")

            # -----------------------------------------
            #   GRÁFICO DE BARRA VERTICAL + LINHA DE META
            # -----------------------------------------
            def formatar_valor_si(valor):
                if valor >= 1_000_000_000:
                    return f"R${valor/1_000_000_000:.1f}B"
                elif valor >= 1_000_000:
                    return f"R${valor/1_000_000:.1f}M"
                elif valor >= 1_000:
                    return f"R${valor/1_000:.1f}K"
                else:
                    return f"R${valor:,.0f}"


            fig_bar = go.Figure()

        # Preparar os dados
            df = orc_geral_filtrado.copy()
            nf_total = df['nota_fiscal_aquisicao'].sum() + df['nota_fiscal_servico'].sum()
            meta_total = df['orcamento_aprovado'].sum()

                # Barra vertical: NF Total
            fig_bar.add_trace(go.Bar(
                    x=['NF Total'],
                    y=[nf_total],
                    marker_color='#1E90FF',
                    name='NF Total (Aquisição + Serviço)',
                    text=[formatar_valor_si(nf_total)],
                    textposition='outside',
                    textfont=dict(size=14),
                    width=0.5
                ))

                # Linha horizontal da meta (Orçamento Aprovado)
            fig_bar.add_hline(
                    y=meta_total,
                    line_dash="solid",
                    line_color="red",
                    line_width=3,
                    annotation_text=f"Meta (Orçamento Aprovado): {formatar_valor_si(meta_total)}",
                    annotation_position="top right",
                    annotation_font_size=12,
                    annotation_font_color="red",
                    annotation_bgcolor="white",
                    annotation_bordercolor="red"
                )

                # Layout
            fig_bar.update_layout(
                    title="NF Total vs Meta Geral de Orçamento Aprovado",
                    yaxis_title="Valor (R$)",
                    xaxis_title="",
                    height=400,
                    template="simple_white",
                    showlegend=True,
                    bargap=0.5,
                    margin=dict(t=50, b=50, l=50, r=50),
                    yaxis=dict(
                        tickformat="~s",      # K, M, B automáticos
                        ticksuffix=" R$",     # símbolo monetário
                        gridcolor='lightgray',
                        range=[0, meta_total * 1.15]
                    ),
                    hovermode="x unified"
                )

            st.plotly_chart(fig_bar, use_container_width=True)


        #================================================================
        
        st.subheader("📊 Gráfico 2.2: Orçamento Aprovado vs Despesa de Aquisição e Serviço")

            # --- Preparar os dados filtrados ---
        df = orc_geral_filtrado.copy()

            # Criar coluna com a soma das notas fiscais
        df['nf_total'] = df['nota_fiscal_aquisicao'] + df['nota_fiscal_servico']

            # Função para formatar valores em milhões/bilhões
        def formatar_valor(valor):
            if valor >= 1_000_000_000:
                return f"R$ {valor/1_000_000_000:.1f}B"
            elif valor >= 1_000_000:
                return f"R$ {valor/1_000_000:.1f}M"
            elif valor >= 1_000:
                return f"R$ {valor/1_000:.0f}K"
            else:
                return f"R$ {valor:,.0f}"

            # --- Construir o gráfico ---
        fig = go.Figure()

            # Barras: NF Total por diretoria
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['nf_total'],
            name='NF Total (Aquisição + Serviço)',
            marker_color='#1E90FF',
            text=[formatar_valor(v) for v in df['nf_total']],
            textposition='outside'
            ))

            # Linha: Orçamento Aprovado por diretoria
        fig.add_trace(go.Scatter(
            x=df['diretoria'],
            y=df['orcamento_aprovado'],
            name='Meta (Orçamento Aprovado)',
            mode='lines+markers+text',
            line=dict(color='red', width=3, shape='spline'),
            marker=dict(size=8, color='red'),
            text=[formatar_valor(v) for v in df['orcamento_aprovado']],
            textposition="top center"
            ))

            # Layout do gráfico
        fig.update_layout(
            title="NF Total vs Meta de Orçamento Aprovado por Diretoria",
            xaxis_title="Diretoria",
            yaxis_title="Valor (R$)",
            template="plotly_white",
            height=600,
            legend_title="Legenda",
            )

            # Formatação do eixo Y em milhões/bilhões
        fig.update_yaxes(
            tickprefix="R$",
            tickformat=".2s",  # Formato científico abreviado (1.2M, 150K, etc.)
            separatethousands=True
            )

            # Exibir no Streamlit
        st.plotly_chart(fig, use_container_width=True)

   
       



        # ------------- TABELA ABAIXO DOS GRÁFICOS --------------------------
        st.markdown("---")  # Linha separadora
        st.subheader("📋 Tabela de Dados - Visão Geral")

    # Criar uma tabela resumo com os valores principais
    if not orc_geral_filtrado.empty:
        st.write("**Resumo de Valores (Geral):**")

        # --- Calcular valores gerais ---
        orcamento_geral = orc_geral_filtrado['orcamento_aprovado'].sum()
        nf_total_geral = (
            orc_geral_filtrado['nota_fiscal_aquisicao'].sum() +
            orc_geral_filtrado['nota_fiscal_servico'].sum()
        )
        saldo_disponivel = orcamento_geral - nf_total_geral
        perc_consumido = (nf_total_geral / orcamento_geral * 100) if orcamento_geral > 0 else 0

        # --- Criar DataFrame de resumo ---
        resumo_data = {
            'Item': [
                'Orçamento Aprovado (Geral)',
                'NF Total (Aquisição + Serviço)',
                'Saldo Disponível',
                'Percentual Consumido'
            ],
            'Valor (R$)': [
                f"R$ {orcamento_geral:,.2f}",
                f"R$ {nf_total_geral:,.2f}",
                f"R$ {saldo_disponivel:,.2f}",
                f"{perc_consumido:.1f}%"
            ]
        }

        resumo_df = pd.DataFrame(resumo_data)

        # Mostrar tabela de resumo
        st.dataframe(resumo_df, use_container_width=True)

            
            # Mostrar tabela original abaixo
            #st.write("**Tabela Detalhada:**")
            #st.dataframe(orc_geral_filtrado, use_container_width=True, height=300)
        #else:
            #st.warning("Nenhum dado disponível para os filtros selecionados")

#----------------------------------------------------------------------
#-----------------------------ABA 2---------------------------------------
with tab2:
    st.header("Análise de Aquisições")
    
    if data['orcamento_geral'].empty:
        st.warning("📝 Dados de orçamento geral não disponíveis")
    else:
        orc_geral_filtrado = aplicar_filtros(data['orcamento_geral'], 'diretoria', diretoria_selecionada)
        
        # KPIs de Aquisições
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_ordens_compra = orc_geral_filtrado['ordens_de_compra'].sum()
            st.metric("Total Ordens de Compra", f"R$ {total_ordens_compra:,.2f}")
        
        with col2:
            total_nf_aquisicao = orc_geral_filtrado['nota_fiscal_aquisicao'].sum()
            st.metric("Total NF Aquisição", f"R$ {total_nf_aquisicao:,.2f}")
        
        with col3:
            total_orc_aquisicao = orc_geral_filtrado['orc_aprovado_aquisicao'].sum()
            st.metric("Orçamento Aprovado Aquisição", f"R$ {total_orc_aquisicao:,.2f}")
        
        st.markdown("---")
        #=====================================================================================================
        #=====================================================================================================
        #=====================================================================================================
        #=====================================================================================================
        #=====================================================================================================
        #=====================================================================================================
        # ESPAÇO PARA GRÁFICO 3
        st.subheader("📈 Gráfico 3: Comparação OC e NF vs Meta por Diretoria")
        #st.write(orc_geral_filtrado.columns)

    # ------------------------------------------------
    # ------------------------------------------------
    # FUNÇÃO DO GRÁFICO 3
    # ------------------------------------------------
    def grafico_orcamento_geral_aquisicao(df):

        def abreviar_valor(v):
            if v >= 1_000_000_000:
                return f"{v/1_000_000_000:.1f}B"
            elif v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            elif v >= 1_000:
                return f"{v/1_000:.1f}K"
            else:
                return f"{v:.0f}"

        fig = go.Figure()

        # --- BARRA 1: Ordens de Compra ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['ordens_de_compra'],  # corrigido
            name='Ordens de Compra',
            marker_color="#1341BE",
            text=[f"R${abreviar_valor(v)}" for v in df['ordens_de_compra']],  # corrigido
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))

        # --- BARRA 2: Nota Fiscal ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['nota_fiscal_aquisicao'],
            name='Nota Fiscal Aquisição',
            marker_color='#79A9FF',
            text=[f"R${abreviar_valor(v)}" for v in df['nota_fiscal_aquisicao']],
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))

        # --- LINHA: Orçamento Aquisição ---
        fig.add_trace(go.Scatter(
            x=df['diretoria'],
            y=df['orc_aprovado_aquisicao'],
            name='Orçamento Aquisição',
            mode='lines+markers+text',
            line=dict(width=3, color='red', shape='spline'),
            marker=dict(size=10, color='#003B73'),
            text=[f"R${abreviar_valor(v)}" for v in df['orc_aprovado_aquisicao']],
            textposition="top center",
            textfont=dict(color='#FFFFFF', size=12)
        ))

        # Layout geral
        fig.update_layout(
            title="Aquisições por Diretoria",
            xaxis_title="Diretoria",
            yaxis_title="Valores (R$)",
            barmode='group',
            template="plotly_dark",
            legend_title="Legenda",
            height=600 
        )

        # --------- FORMATAÇÃO DOS NÚMEROS ---------
        fig.update_yaxes(
            tickprefix="R$",
            separatethousands=True,
            tickformat=".2s"  # 15M, 1.2M, 200K...
        )

        return fig
   


    # ------------------------------------------------
    # CONTAINER DO GRÁFICO
    # ------------------------------------------------
    with st.container():
        fig = grafico_orcamento_geral_aquisicao(orc_geral_filtrado)  # corrigido
        st.plotly_chart(fig, use_container_width=True)

        
        
        #==============================================================
        st.markdown("---")
    # ESPAÇO PARA GRÁFICO 3.1
        st.subheader("📈 Gráfico 3.1: Aquisição Mensal por Diretoria")
        # ===============================


       

        df_nf = data['nf_de_aquisicao'].copy()

        if df_nf.empty:
            st.warning("📝 Dados de NF de Aquisição não disponíveis")
        else:
            # Meses no padrão do Excel
            meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
                    'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

            meses_existentes = [m for m in meses if m in df_nf.columns]

            if not meses_existentes:
                st.error("❌ Colunas mensais (JAN–DEZ) não encontradas")
            else:
                # Aplicar filtro de diretoria (sua função)
                df_nf = aplicar_filtros(df_nf, 'DIRETORIA', diretoria_selecionada)

                # 🔄 Transformar meses em linhas
                df_long = df_nf.melt(
                    id_vars=['DIRETORIA'],
                    value_vars=meses_existentes,
                    var_name='MES',
                    value_name='VALOR'
                )

                # Remover valores nulos
                df_long = df_long.dropna(subset=['VALOR'])

                # Ordem correta dos meses
                ordem_meses = {mes: i for i, mes in enumerate(meses)}
                df_long['ordem_mes'] = df_long['MES'].map(ordem_meses)
                df_long = df_long.sort_values('ordem_mes')

                # Gráfico de linha por diretoria
                fig = px.line(
                    df_long,
                    x='MES',
                    y='VALOR',
                    color='DIRETORIA',   # 🎯 UMA LINHA POR DIRETORIA
                    markers=True,
                    line_shape="spline",
                    title="Evolução Mensal dos Gastos com Aquisições",
                    labels={
                        'MES': 'Mês',
                        'VALOR': 'Valor (R$)',
                        'DIRETORIA': 'Diretoria'
                    }
                )
                ordem_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
               'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

                fig.update_xaxes(
                    categoryorder='array',
                    categoryarray=ordem_meses
                )


                fig.update_layout(
                    template="simple_white",
                    height=450,
                    hovermode="x unified",
                    yaxis_tickformat="~s",
                    legend_title_text="Diretorias"
                )

                fig.update_traces(
                    line=dict(width=3, shape="spline"),
                    marker=dict(size=7)
                )

                st.plotly_chart(fig, use_container_width=True)




        st.markdown("---")

        #==============================================================
        # ESPAÇO PARA GRÁFICO 4
        st.subheader("📊 Gráfico 4: Distribuição de Valores de NF por Classificação de Rateio")
        # ============================================================
        # 📊 GRÁFICO 4 – Distribuição de Valores de NF por Rateio
        # ============================================================

        # Verificar quais abas estão disponíveis no dicionário data
        # st.write("### 🗂️ Abas disponíveis na planilha:")
        # aba_list = list(data.keys())
        # st.write(aba_list)

        # # Mostrar nome da quinta aba especificamente
        # if len(aba_list) >= 5:
        #     st.info(f"A quinta aba se chama: **'{aba_list[4]}'**")

#------------- GRÁFICO 4 – DONUT / PIZZA -----------------------
#st.subheader("📊 Gráfico 4: Distribuição de Valores de NF por Classificação de Rateio")

        # Filtra base da aba ORDENS_DE_COMPRA
        if "ordens_de_compra" not in data or data["ordens_de_compra"].empty:
            st.warning("⚠ Nenhum dado disponível em 'ordens_de_compra' para gerar o gráfico.")
        else:
            df_rateio = data["ordens_de_compra"]

            # Agrupando valores por classificação de rateio
            df_grouped = (
                df_rateio.groupby("Nome Classif. Rateio")["Vlr. Total NF"]
                .sum()
                .reset_index()
                .sort_values("Vlr. Total NF", ascending=False)       # ordena do maior para o menor
            )

            # Criar gráfico de rosca
            fig_donut = go.Figure(
                go.Pie(
                    labels=df_grouped["Nome Classif. Rateio"],
                    values=df_grouped["Vlr. Total NF"],
                    hole=0.45,  # tamanho do furo
                    textinfo="percent+label",
                    textfont=dict(size=13),
                    hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<extra></extra>",
                    sort=False,  # mantém a ordem definida acima
                )
            )

            fig_donut.update_layout(
                title="Distribuição Percentual dos Valores de NF por Tipo de Rateio",
                height=600,
                legend_title="Classificação de Rateio",
                margin=dict(t=60, b=20, l=10, r=10),
            )

            fig_donut.update_traces(
                textinfo="percent",
            )

            st.plotly_chart(fig_donut, use_container_width=True)
        #----------------------------------------------------------------
               # -------------------------------------------------------------------
            # Mostrar tabela com dados utilizados
            st.caption("📄 **Dados utilizados no gráfico:**")
            st.dataframe(df_grouped, use_container_width=True)


                    
            #         # Mostrar dados disponíveis para o gráfico
            # if not data['ordens_de_compra'].empty:
            #             ordens_compra_filtrado = aplicar_filtros(data['ordens_de_compra'], 'diretoria', diretoria_selecionada)
            #             if not ordens_compra_filtrado.empty:
            #                 st.caption("Dados disponíveis para o gráfico:")
            #                 rateio_soma = ordens_compra_filtrado.groupby('Nome Classif. Rateio')['Vlr. Total NF'].sum()
            #                 st.write(rateio_soma)
            # else:
            #             st.warning("Dados de ordens de compra não disponíveis")

#----------------------------------------------------------------------
#-----------------------------ABA 3---------------------------------------
with tab3:
    st.header("Análise de Serviços")
    
    if data['orcamento_geral'].empty:
        st.warning("📝 Dados de orçamento geral não disponíveis")
    else:
        orc_geral_filtrado = aplicar_filtros(data['orcamento_geral'], 'diretoria', diretoria_selecionada)
        
        # KPIs de Serviços
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_ordens_servico = orc_geral_filtrado['ordens_de_servico'].sum()
            st.metric("Total Ordens de Serviço", f"R$ {total_ordens_servico:,.2f}")
        
        with col2:
            total_nf_servico = orc_geral_filtrado['nota_fiscal_servico'].sum()
            st.metric("Total NF Serviço", f"R$ {total_nf_servico:,.2f}")
        
        with col3:
            total_orc_servico = orc_geral_filtrado['orc_aprovado_servico'].sum()
            st.metric("Orçamento Aprovado Serviço", f"R$ {total_orc_servico:,.2f}")
        
        st.markdown("---")
        
        # ESPAÇO PARA GRÁFICO 5
        st.subheader("📈 Gráfico 5: Comparação Serviços vs Meta por Diretoria")
        
        # ------------------------------------------------
    # FUNÇÃO DO GRÁFICO 5
    # ------------------------------------------------
    def grafico_orcamento_geral_aquisicao(df):

        def abreviar_valor(v):
            if v >= 1_000_000_000:
                return f"{v/1_000_000_000:.1f}B"
            elif v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            elif v >= 1_000:
                return f"{v/1_000:.1f}K"
            else:
                return f"{v:.0f}"

        fig = go.Figure()

        # --- BARRA 1: Ordens de Serviço ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['ordens_de_servico'],  # corrigido
            name='Ordens de Serviço',
            marker_color="#1341BE",
            text=[f"R${abreviar_valor(v)}" for v in df['ordens_de_servico']],
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))

        # --- BARRA 2: Nota Fiscal Serviço ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['nota_fiscal_servico'],
            name='Nota Fiscal Serviço',
            marker_color='#79A9FF',
            text=[f"R${abreviar_valor(v)}" for v in df['nota_fiscal_servico']],
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))

        # --- LINHA: Orçamento Serviço ---
        fig.add_trace(go.Scatter(
            x=df['diretoria'],
            y=df['orc_aprovado_servico'],
            name='Orçamento Serviço',
            mode='lines+markers+text',
            line=dict(width=3, color='red', shape='spline'),
            marker=dict(size=10, color='#003B73'),
            text=[f"R${abreviar_valor(v)}" for v in df['orc_aprovado_servico']],
            textposition="top center",
            textfont=dict(color='#FFFFFF', size=12)
        ))

        # Layout geral
        fig.update_layout(
            title="Aquisições por Diretoria",
            xaxis_title="Diretoria",
            yaxis_title="Valores (R$)",
            barmode='group',
            template="plotly_dark",
            legend_title="Legenda",
            height=600 
        )

        # --------- FORMATAÇÃO DOS NÚMEROS ---------
        fig.update_yaxes(
            tickprefix="R$",
            separatethousands=True,
            tickformat=".2s"  # 15M, 1.2M, 200K...
        )

        return fig
   


    # ------------------------------------------------
    # CONTAINER DO GRÁFICO
    # ------------------------------------------------
    with st.container():
        fig = grafico_orcamento_geral_aquisicao(orc_geral_filtrado)  # corrigido
        st.plotly_chart(fig, use_container_width=True)


        
        st.markdown("---")


    # ESPAÇO PARA GRÁFICO 5.1
        st.subheader("📈 Gráfico 5.1: Serviço Mensal por Diretoria")
        # ===============================


       

        df_nf_srv = data['nf_de_servico'].copy()

        if df_nf_srv.empty:
            st.warning("📝 Dados de NF de Serviço não disponíveis")
        else:
            # Meses no padrão do Excel
            meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
                    'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

            meses_existentes = [m for m in meses if m in df_nf_srv.columns]

            if not meses_existentes:
                st.error("❌ Colunas mensais (JAN–DEZ) não encontradas")
            else:
                # Aplicar filtro de diretoria
                df_nf_srv = aplicar_filtros(df_nf_srv, 'DIRETORIA', diretoria_selecionada)

                # 🔄 Transformar meses em linhas
                df_long_srv = df_nf_srv.melt(
                    id_vars=['DIRETORIA'],
                    value_vars=meses_existentes,
                    var_name='MES',
                    value_name='VALOR'
                ).dropna(subset=['VALOR'])

                # Gráfico de linha por diretoria (curvas)
                fig_srv = px.line(
                    df_long_srv,
                    x='MES',
                    y='VALOR',
                    color='DIRETORIA',
                    markers=True,
                    line_shape="spline",
                    title="Evolução Mensal dos Gastos com Serviços",
                    labels={
                        'MES': 'Mês',
                        'VALOR': 'Valor (R$)',
                        'DIRETORIA': 'Diretoria'
                    }
                )

                # 🎯 Forçar ordem correta dos meses
                fig_srv.update_xaxes(
                    categoryorder='array',
                    categoryarray=meses
                )

                fig_srv.update_layout(
                    template="simple_white",
                    height=450,
                    hovermode="x unified",
                    yaxis_tickformat="~s",
                    legend_title_text="Diretorias"
                )

                fig_srv.update_traces(
                    line=dict(width=3, shape="spline"),
                    marker=dict(size=7)
                )

                st.plotly_chart(fig_srv, use_container_width=True)




        st.markdown("---")

        
        # Tabela de dados de serviços
        st.subheader("📋 Dados Detalhados de Serviços")
        if not orc_geral_filtrado.empty:
            # Selecionar colunas relevantes para serviços
            cols_servicos = ['diretoria', 'ordens_de_servico', 'nota_fiscal_servico', 
                           'orc_aprovado_servico']
            if all(col in orc_geral_filtrado.columns for col in cols_servicos):
                df_servicos = orc_geral_filtrado[cols_servicos].copy()
                # Formatar valores monetários
                for col in ['orc_aprovado_servico', 'fora_do_plano']:
                    if col in df_servicos.columns:
                        df_servicos[col] = df_servicos[col].apply(lambda x: f'R$ {x:,.2f}')
                st.dataframe(df_servicos, use_container_width=True)
            else:
                st.warning("Colunas de serviços não encontradas no DataFrame")
        else:
            st.warning("Nenhum dado disponível para os filtros selecionados")

#----------------------------------------------------------------------
#-----------------------------ABA 4---------------------------------------
with tab4:
    st.header("Análise Detalhada")
    
    # --- Garantir que a variável exista sempre ---
    if 'nao_planejado' not in data or data['nao_planejado'] is None:
        # cria DataFrame vazio para evitar NameError
        nao_planejado_filtrado = pd.DataFrame()
    elif data['nao_planejado'].empty:
        nao_planejado_filtrado = pd.DataFrame()
    else:
        # aplica filtros assim que possível
        nao_planejado_filtrado = aplicar_filtros(
            data['nao_planejado'], 'diretoria', diretoria_selecionada
        )



    # --- MÉTRICA AQUI ---
    if not nao_planejado_filtrado.empty:
            total_nao_planejado = nao_planejado_filtrado['valor_total'].sum()
            st.metric("💰 Total de Itens Não Planejados", f"R$ {total_nao_planejado:,.2f}")
        # ---------------------

    # Tabela de Itens Não Planejados
    st.subheader("📋 Itens Não Planejados")
    st.markdown("Ocultado")
    
    # if data['nao_planejado'].empty:
    #     st.warning("📝 Dados de itens não planejados não disponíveis")
    # else:
    #     nao_planejado_filtrado = aplicar_filtros(data['nao_planejado'], 'diretoria', diretoria_selecionada)
        
    #     if nao_planejado_filtrado.empty:
    #         st.warning("📊 Nenhum item não planejado para os filtros selecionados")
    #     else:
    #         tabela_exibicao = nao_planejado_filtrado[[
    #             'diretoria', 'fornecedor', 'descricao', 'quantidade', 
    #             'mes_compra', 'valor_total', 'situacao'
    #         ]].copy()
            
    #         tabela_exibicao['valor_total'] = tabela_exibicao['valor_total'].apply(lambda x: f'R$ {x:,.2f}')
            
    #         st.dataframe(tabela_exibicao, use_container_width=True)
    
    st.markdown("---")
    
    # ESPAÇO PARA GRÁFICO ADICIONAL (se necessário)
    st.subheader("📊 Gráfico Aquisições Não Planejado")
    # FUNÇÃO DO GRÁFICO 5
    # ------------------------------------------------
    def grafico_fora_do_plano(df):

        def abreviar_valor(v):
            if v >= 1_000_000_000:
                return f"{v/1_000_000_000:.1f}B"
            elif v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            elif v >= 1_000:
                return f"{v/1_000:.1f}K"
            else:
                return f"{v:.0f}"

        fig = go.Figure()

        # --- BARRA 1: NF de Aquisição ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['nota_fiscal_aquisicao'],  # corrigido
            name='NF de Aquisição',
            marker_color="#13C7E2",
            text=[f"R${abreviar_valor(v)}" for v in df['nota_fiscal_aquisicao']],
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))



	# --- BARRA 3: Não Planejado ---
        fig.add_trace(go.Bar(
            x=df['diretoria'],
            y=df['fora_do_plano'],
            name='Não Planejado',
            marker_color="#DB1A1A",
            text=[f"R${abreviar_valor(v)}" for v in df['fora_do_plano']],
            textposition='outside',
            textfont=dict(color='white', size=12)
        ))

        # --- LINHA: Orçamento Geral ---
        fig.add_trace(go.Scatter(
            x=df['diretoria'],
            y=df['orcamento_aprovado'],
            name='Orçamento aprovado',
            mode='lines+markers+text',
            line=dict(width=3, color='green', shape='spline'),
            marker=dict(size=10, color="#032D03"),
            text=[f"R${abreviar_valor(v)}" for v in df['orcamento_aprovado']],
            textposition="top center",
            textfont=dict(color='#FFFFFF', size=12)
        ))

        # Layout geral
        fig.update_layout(
            title="Aquisições por Diretoria",
            xaxis_title="Diretoria",
            yaxis_title="Valores (R$)",
            barmode='group',
            template="plotly_dark",
            legend_title="Legenda",
            height=600 
        )

        # --------- FORMATAÇÃO DOS NÚMEROS ---------
        fig.update_yaxes(
            tickprefix="R$",
            separatethousands=True,
            tickformat=".2s"  # 15M, 1.2M, 200K...
        )

        return fig
   


    # ------------------------------------------------
    # CONTAINER DO GRÁFICO
    # ------------------------------------------------
    with st.container():
        fig = grafico_fora_do_plano(orc_geral_filtrado)  # corrigido
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Insights e Recomendações
    st.subheader("💡 Insights e Recomendações")
    
    if data['orcamento_geral'].empty or data['nao_planejado'].empty:
        st.warning("📊 Dados insuficientes para gerar insights")
    else:
        orc_geral_filtrado = aplicar_filtros(data['orcamento_geral'], 'diretoria', diretoria_selecionada)
        nao_planejado_filtrado = aplicar_filtros(data['nao_planejado'], 'diretoria', diretoria_selecionada)
        
        total_planejado = orc_geral_filtrado['orcamento_planejado'].sum()
        total_aprovado = orc_geral_filtrado['orcamento_aprovado'].sum()
        total_fora_plano = orc_geral_filtrado['fora_do_plano'].sum()
        
        if nao_planejado_filtrado.empty:
            total_nao_planejado = 0
        else:
            total_nao_planejado = nao_planejado_filtrado['valor_total'].sum()
        
        # Calcular percentuais
        percentual_fora_plano = (total_fora_plano / total_aprovado) * 100 if total_aprovado > 0 else 0
        percentual_nao_planejado = (total_nao_planejado / total_aprovado) * 100 if total_aprovado > 0 else 0
        
        insights = []
        
        if percentual_fora_plano > 15:
            insights.append("⚠️ **Alto percentual de gastos fora do plano** ({:.1f}%) - Revisar processos de planejamento".format(percentual_fora_plano))
        else:
            insights.append("✅ **Bom controle de gastos fora do plano** ({:.1f}%)".format(percentual_fora_plano))
        
        if percentual_nao_planejado > 10:
            insights.append("⚠️ **Alto percentual de gastos não planejados** ({:.1f}%) - Fortalecer processos de compras planejadas".format(percentual_nao_planejado))
        else:
            insights.append("✅ **Bom controle de gastos não planejados** ({:.1f}%)".format(percentual_nao_planejado))
        
        if not nao_planejado_filtrado.empty:
            diretoria_maior_gasto = nao_planejado_filtrado.groupby('diretoria')['valor_total'].sum().idxmax()
            valor_maior_gasto = nao_planejado_filtrado.groupby('diretoria')['valor_total'].sum().max()
            insights.append("📊 **{} tem o maior gasto não planejado** - R$ {:,.2f}".format(diretoria_maior_gasto, valor_maior_gasto))
        
        taxa_execucao = (total_aprovado - total_fora_plano) / total_aprovado * 100 if total_aprovado > 0 else 0
        if taxa_execucao > 80:
            insights.append("✅ **Alta eficiência na execução orçamentária** ({:.1f}% do orçamento utilizado conforme planejado)".format(taxa_execucao))
        else:
            insights.append("⚠️ **Baixa eficiência na execução orçamentária** ({:.1f}% do orçamento utilizado conforme planejado)".format(taxa_execucao))
        
        for insight in insights:
            if "⚠️" in insight:
                st.warning(insight)
            elif "📊" in insight:
                st.info(insight)
            else:
                st.success(insight)

# Status do carregamento na sidebar
st.sidebar.header("📊 Status do Carregamento")
abas_carregadas = sum(1 for df in data.values() if not df.empty)
st.sidebar.info(f"**{abas_carregadas} de {len(data)} abas** carregadas com sucesso")

# Informações sobre os gráficos
st.sidebar.header("projeto")
st.sidebar.info("""
**dados:**

- **Contato:** mafradebora26@gmail.com

)

""")
st.sidebar.header("📅 Última Atualização")
st.sidebar.info(f"Os dados foram atualizados em: **{datetime.now().strftime('%d/%m/%Y %H:%M')}**")

# Rodapé
st.markdown("---")
st.markdown("**2025**")