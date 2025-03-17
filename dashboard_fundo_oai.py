import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# Caminho do arquivo Excel
file_path = "fundo_oai.xlsx"


def get_sol_price():
    """Obtém o preço atual da Solana da API."""
    url = "https://frontend-api.pump.fun/sol-price"
    try:
        response = requests.get(url, timeout=5)  # Timeout de 5 segundos
        response.raise_for_status()  # Levanta um erro para status HTTP ruim
        data = response.json()  # Converte a resposta para JSON
        return data.get("solPrice", 0)  # Retorna o preço ou 0 se não encontrar
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar preço da Solana: {e}")
        return 0  # Retorna 0 em caso de erro

def read_data():
    """Lê os dados do Excel e retorna um DataFrame."""
    try:
        df = pd.read_excel(file_path)
        df['Sol Investida'] = pd.to_numeric(df['Sol Investida'], errors='coerce').fillna(0)
        df['Sol Retirada'] = pd.to_numeric(df['Sol Retirada'], errors='coerce').fillna(0)
        df['USDT Investido'] = pd.to_numeric(df['USDT Investido'], errors='coerce').fillna(0).round(2)
        df['USDT Retirado'] = pd.to_numeric(df['USDT Retirado'], errors='coerce').fillna(0).round(2)
        df['Rendimento em Sol'] = (df['Sol Retirada'] - df['Sol Investida']).fillna(0).round(4)
        df['Rendimento em USDT'] = (df['USDT Retirado'] - df['USDT Investido'].fillna(0)).round(2)
    

        # Criar uma coluna numérica para condicional
        df['Rendimento USDT %'] = ((df['Rendimento em USDT'] / df['USDT Investido']) * 100).round(2).astype(str) + ' %'


        capital_inicial_sol = df['Solana investida'].iloc[0] if 'Solana investida' in df.columns and len(df) > 0 else 0


        df['Rendimento Percentual Acumulado Sol (%)'] = ((df['Rendimento em Sol'].cumsum()) / capital_inicial_sol) * 100
        df['Rendimento Percentual Acumulado Sol (%)'] = df['Rendimento Percentual Acumulado Sol (%)'].round(2)




        # df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%d/%m/%Y')  # Formata data para dd/mm/yyyy
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        # df = df.sort_values(by='Data')
        # df['Rendimento Acumulado USDT'] = df['Rendimento em USDT'].cumsum()
        df['Rendimento Acumulado Sol'] = df['Rendimento em Sol'].cumsum()  # Novo cálculo para SOL
        valor_investido_fundo = df['Investimento USDT'].iloc[0] if 'Investimento USDT' in df.columns and len(df) > 0 else 0

        # Obtendo o preço da Solana via API
        cotacao_sol = get_sol_price()

        # Novo cálculo de rendimento acumulado em USDT com base na cotação da SOL
        df['Rendimento liquido USDT'] = (df['Rendimento em Sol'] * cotacao_sol).round(2)
        df['Rendimento Diario USDT'] = (df['Rendimento em Sol'] * cotacao_sol).round(2)
        df['Rendimento Acumulado USDT'] = df['Rendimento Diario USDT'].cumsum().round(2)
        if len(df) > 1:
            valor_sol = df['Valor Sol Carteira'].iloc[0]  # Segunda linha da coluna N
            capital_atual = valor_sol * cotacao_sol  # Multiplicação para obter o capital
        else:
            capital_atual = 0  # Evita erro se não houver dados suficientes


        return df, valor_investido_fundo, capital_atual
    except Exception as e:
        print("Erro ao ler o arquivo:", e)
        return pd.DataFrame(), 0

# Inicializando o app Dash
app = dash.Dash(__name__)
app.layout = html.Div(style={'backgroundColor': '#12132D', 'color': 'white', 'padding': '20px', 'fontFamily': 'Arial'}, children=[
    html.H1("Dashboard OAI Capital", style={'textAlign': 'center', 'color': '#00CFFF'}),
    
    dcc.Interval(
        id='interval-update',
        interval=5000,  # Atualiza a cada 5 segundos
        n_intervals=0
    ),
    
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
        dcc.Graph(id='grafico-linha-sol'),
        dcc.Graph(id='grafico-linha')
    ]),

    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
        dcc.Graph(id='grafico-pizza'),
        dcc.Graph(id='grafico-trades-positivos')
    ]),

    html.Div(style={'display': '100%', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
        dcc.Graph(id='grafico-barras-lucro')  # Novo gráfico de barras de lucro
    ]),

    
    html.Div(style={'display': '100%', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'alignItems': 'start'}, children=[
        dash_table.DataTable(id='tabela-trades',
            style_table={'overflowX': 'auto', 'backgroundColor': '#1E1E2F', 'width': '100%'},
            style_header={'backgroundColor': '#333', 'color': 'white', 'fontWeight': 'bold'},
            style_data={'backgroundColor': '#1E1E2F', 'color': 'white'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Rendimento em Sol} > 0', 'column_id': 'Rendimento em Sol'},
                    'color': 'lightgreen'
                },
                {
                    'if': {'filter_query': '{Rendimento em Sol} < 0', 'column_id': 'Rendimento em Sol'},
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Rendimento em USDT} > 0', 'column_id': 'Rendimento em USDT'},
                    'color': 'lightgreen'
                },
                {
                    'if': {'filter_query': '{Rendimento em USDT} < 0', 'column_id': 'Rendimento em USDT'},
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Rendimento USDT %} > 0%', 'column_id': 'Rendimento USDT %'},
                    'color': 'lightgreen'
                },
                {
                    'if': {'filter_query': '{Rendimento USDT %} < 0%', 'column_id': 'Rendimento USDT %'},
                    'color': 'red'
                }
                
            ],
            style_cell={
                'textAlign': 'center',
                'padding': '5px',
                'minWidth': '100px', 'maxWidth': '180px', 'whiteSpace': 'normal'
            }
        ),
        
    ])
])

@app.callback(
    [Output('grafico-linha', 'figure'),
     Output('grafico-linha-sol', 'figure'),
     Output('grafico-pizza', 'figure'),
     Output('tabela-trades', 'data'),
     Output('tabela-trades', 'columns'),
     Output('grafico-trades-positivos', 'figure'),
     Output('grafico-barras-lucro', 'figure')],
    Input('interval-update', 'n_intervals')
)
def update_dashboard(n):
    df, valor_investido_fundo, capital_atual = read_data()
    if df.empty:
        return px.Figure(), px.Figure(), [], [], px.Figure()
    
    layout_dark = dict(plot_bgcolor='#1E1E2F', paper_bgcolor='#1E1E2F', font=dict(color='white'))
    
    fig_linha = go.Figure()
    fig_linha.add_trace(go.Scatter(x=df['Data'], y=df['Rendimento Percentual Acumulado Sol (%)'], mode='lines', name='RRendimento Percentual Acumulado Sol (%)'))
    fig_linha.update_layout(title='Porcentagem de lucro em SOL', **layout_dark)
    
    fig_linha.add_annotation(
        x=1.05,
        y=df['Rendimento Percentual Acumulado Sol (%)'].iloc[-1],
        xref='paper', 
        text=f" {df['Rendimento Percentual Acumulado Sol (%)'].iloc[-1]:,.2f}%", 
        showarrow=False,
        font=dict(size=14, color="white"),
        xanchor='right',
        yanchor='middle',
        xshift=30,  # Move a anotação para a lateral direita
        bgcolor='#1E1E2F',
        bordercolor='white',
        borderwidth=2
    )
    
    

    # Gráfico de linha para SOL
    fig_linha_sol = go.Figure()
    fig_linha_sol.add_trace(go.Scatter(x=df['Data'], y=df['Rendimento Acumulado Sol'], mode='lines', name='Rendimento Acumulado Sol', line=dict(color='yellow')))
    fig_linha_sol.update_layout(title='Rendimento Acumulado em SOL e USDT', **layout_dark)

    fig_linha_sol.add_annotation(
        x=1.05,
        xref='paper',
        y=df['Rendimento Acumulado Sol'].iloc[-1],
        text=f"{df['Rendimento Acumulado Sol'].iloc[-1]:,.2f} SOL<br>${df['Rendimento Acumulado USDT'].iloc[-1]:,.2f}",
        showarrow=False,
        font=dict(size=14, color="white"),
        xanchor='right',
        yanchor='middle',
        xshift=30,  # Move a anotação para a lateral direita
        bgcolor='#1E1E2F',
        bordercolor='white',
        borderwidth=2
    )


    
    total_investido = valor_investido_fundo
    total_lucro = df['Rendimento liquido USDT'].sum()
    valores = [total_investido, total_lucro, capital_atual]
    nomes = [f'Capital Investido: ${total_investido:,.2f}', f'Lucro: ${total_lucro:,.2f}', f'Capital Atual: ${capital_atual:,.2f}']
    fig_pizza = px.pie(names=nomes, values=valores, title='Distribuição de Capital', hole=0.4)
    fig_pizza.update_traces(textfont=dict(size=16, color='white', family='Arial Black'))
    fig_pizza.update_layout(**layout_dark)
    
    
    
    num_trades = len(df)
    trades_positivos = len(df[df['Rendimento em USDT'] > 0])
    trades_negativos = num_trades - trades_positivos
    fig_trades = px.pie(names=['Trades Positivos', 'Trades Negativos'], values=[trades_positivos, trades_negativos],
                     title='Percentual de Trades Positivos e Negativos')
    fig_trades.update_traces(textfont=dict(size=16, color='white', family='Arial Black'))
    fig_trades.update_layout(**layout_dark)

     # Gráfico de barras (Lucro Diário em SOL e USDT)
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(x=df['Data'], y=df['Rendimento em USDT'], name='Lucro USDT', marker_color='cyan'))
    fig_barras.add_trace(go.Bar(x=df['Data'], y=df['Rendimento em Sol'], name='Lucro SOL', marker_color='yellow'))
    fig_barras.update_layout(title='Lucro Diário (SOL e USDT)', barmode='group', **layout_dark)
    
    # Gráfico de barras (Lucro Diário em SOL e USDT)

    
    # fig_barras = go.Figure()
    fig_barras = make_subplots(rows=1, cols=2, shared_xaxes=True, subplot_titles=("Lucro em USDT", "Lucro em SOL"))

    # Agrupar dados por Data para somar os rendimentos do dia
          
    df_agrupado = df.groupby('Data', as_index=False).sum(numeric_only=True)
    df_agrupado = df_agrupado.sort_values(by='Data')

    # Lucro em USDT (Gráfico à esquerda)
    fig_barras.add_trace(go.Bar(
        x=df_agrupado['Data'], 
        y=df_agrupado['Rendimento em USDT'], 
        name='Lucro USDT', 
        marker_color='cyan',
        text=df_agrupado['Rendimento em USDT'].apply(lambda x: f"{x:,.2f}"),
        textposition='outside'
    ), row=1, col=1)

    # Lucro em SOL (Gráfico à direita)
    fig_barras.add_trace(go.Bar(
        x=df_agrupado['Data'], 
        y=df_agrupado['Rendimento em Sol'], 
        name='Lucro SOL', 
        marker_color='yellow',
        text=df_agrupado['Rendimento em Sol'].apply(lambda x: f"{x:.2f}"),
        textposition='outside'
    ), row=1, col=2)

    # Configuração do layout
    fig_barras.update_layout(
    title='Lucro Diário (SOL e USDT)', 
    barmode='group',  # Coloca as barras lado a lado
    xaxis_title='Data',
    yaxis_title='Lucro',
    showlegend=True,
    **layout_dark
    )

    # Após adicionar os traces, adicionamos anotações para cada ponto
    # for i, row in df_agrupado.iterrows():
    #     fig_barras.add_annotation(
    #         x=row['Data'],
    #         y=row['Rendimento em USDT'],
    #         text=f"${row['Rendimento em USDT']:,.2f}",
    #         showarrow=False,
    #         font=dict(size=10, color="white"),  # Aumente conforme necessário
    #         yshift=35  # Ajuste a posição vertical do texto
    #     )

        # fig_barras.add_annotation(
        #     x=row['Data'],
        #     y=row['Rendimento em Sol'],
        #     text=f"{row['Rendimento em Sol']:.2f} SOL",
        #     showarrow=False,
        #     font=dict(size=20, color="white"),
        #     yshift=10
        # )

    # Aumentando o tamanho da fonte dos valores
    # fig_barras.update_traces(textfont=dict(size=26))
    # fig_barras.update_traces(textfont=dict(size=16), textposition='auto')
    
    df['USDT Investido'] = df['USDT Investido'].apply(lambda x: f"{x:,.2f}")
    df['USDT Retirado'] = df['USDT Retirado'].apply(lambda x: f"{x:,.2f}")
    df['Rendimento em USDT'] = df['Rendimento em USDT'].apply(lambda x: f"{x:,.2f}")
    df['Rendimento em Sol'] = df['Rendimento em Sol'].apply(lambda x: f"{x:,.2f}")

    colunas = ["Data", "Pool", "Sol Investida", "USDT Investido", "Sol Retirada", "USDT Retirado", "Rendimento em Sol", "Rendimento em USDT", "Rendimento USDT %"]
    df["Pool"] = df["Pool"].astype(str)  # Garante que a coluna Pool seja string
    dados_tabela = df[colunas].to_dict('records')
    colunas_tabela = [{'name': col, 'id': col} for col in colunas]

       
    return fig_linha, fig_linha_sol, fig_pizza, dados_tabela, colunas_tabela, fig_trades, fig_barras

if __name__ == '__main__':
    app.run_server(debug=True)