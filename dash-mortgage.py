import pandas as pd
import numpy_financial as npf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from datetime import date, datetime
import locale

from dash import Dash, dcc, html, Input, Output, callback

locale.setlocale( locale.LC_ALL, '')

ppy        = 12

#  mortgage amount, interest, term, and extra payment
def make_payment_table(m, i, t, e):
    initial_payment  = -1 * npf.pmt(i/ppy, t*ppy, m)
    initial_ipayment = -1 * npf.ipmt(i/ppy, 1, t*ppy, m)
    initial_ppayment = -1 * npf.ppmt(i/ppy, 1, t*ppy, m)
    
    rng = pd.Series(range(1,1+12*t))
    rng.name = "Payment Date"
    df = pd.DataFrame(
        index=rng,
        columns=['Total Payment',
                 'Interest',
                 'Intereste',                 
                 'Principal',
                 'Principale',                 
                 'Additional Payment',
                 'Ending Balance w/ Extra',
                 'Ending Balance'],
        dtype='float')

    #df.reset_index(inplace=True)
    df.index.name = "Period"
    
    
    # First row (Think of it as the seed for the whole thing)

    period = 1

    initial_seed = {
        'Total Payment'  : initial_payment,
        'Interest'       : initial_ipayment,
        'Principal'      : initial_ppayment,
        'Intereste'       : initial_ipayment,
        'Principale'      : initial_ppayment + e,
        'Additional Payment' : e,
        'Ending Balance w/ Extra' : m - initial_payment - e,
        'Ending Balance'          : m - initial_payment
    }


    df.at[period, initial_seed.keys()] = initial_seed.values()
    df = df.round(2)



    #Populate the rest of the payments table

    for period in range(2, len(df) + 1):
        previous_tp   = df.loc[period - 1, 'Total Payment']
        previous_pr   = df.loc[period - 1, 'Principal']
        previous_end  = df.loc[period - 1, 'Ending Balance']
        previous_ende = df.loc[period - 1, 'Ending Balance w/ Extra']

        period_interest   = previous_end  * i / ppy
        period_intereste  = previous_ende * i / ppy
        period_principal  = initial_payment - period_interest
        period_principale = initial_payment - period_intereste + e
        
        ending_drafte     = previous_ende - period_principale - e
        ending_balancee   = 0 if ending_drafte <= 0 else ending_drafte
        ending_draft      = previous_end - period_principal
        ending_balance    = 0 if ending_draft <= 0 else ending_draft

        row = {
            'Total Payment'  : initial_payment,
            'Interest'       : period_interest,
            'Principal'      : period_principal,
            'Intereste'       : period_intereste,
            'Principale'      : period_principale,
            'Additional Payment' : e,
            'Ending Balance w/ Extra' : ending_balancee,
            'Ending Balance'     : ending_balance
        }

        #df.at[period, row.keys()] = row.values()
        df.loc[period] = pd.Series(row)

    df['Payment Date'] = rng
    return df, initial_payment


loan_amount = dcc.Slider(100000, 1000000, value=550000,
    tooltip={"placement": "top", "always_visible": True},
    marks={
        100000: {'label': '$100,000'},
        200000: {'label': '$200,000'},
        300000: {'label': '$300,000'},
        400000: {'label': '$400,000'},
        500000: {'label': '$500,000'},
        600000: {'label': '$600,000'},
        700000: {'label': '$700,000'},
        800000: {'label': '$800,000'},
        900000: {'label': '$900,000'},
        1000000: {'label': '$1,000,000'}
    },
    id='loan-slider',
    included=False
)

extra_payment = dcc.Slider(0, 5000, value=500,
    tooltip={"placement": "top", "always_visible": True},
    marks={
        0: {'label': '$0'},
        2500: {'label': '$2,500'},
        5000: {'label': '$5,000'},
    },
    id='extra-slider',
    included=False
)

interest_rate = dcc.Slider(0.03, 0.1, value=0.07,
    tooltip={"placement": "top", "always_visible": True},
    marks={
        0.03: {'label': '3%'},
        0.07: {'label': '7%'},
        0.1: {'label': '10%'},
    },
    id='interest-slider',
    included=False
)

term_select = dcc.RadioItems(
    [15, 30],
    15,
    id='term-button',
    inline=True
)

app = Dash(__name__)

app.layout = html.Div([
    html.Div(children='Loan Amount'),
    loan_amount,
    html.Br(),
    html.Div(children='Extra Monthly Payment'),
    extra_payment,
    html.Br(),
    html.Div(children='Mortgage Term'),
    term_select,
    html.Br(),
    html.Div(children='Interest Rate'),
    interest_rate,
    html.Div(id='mp'),
    html.Br(),
    html.Div(id='me'),
    html.Br(),
    html.Div(id='di'),
    html.Br(),
    html.Div(id='ie'),
    dcc.Graph(id='mortgage-plot')

])


@callback(
        Output('mortgage-plot', 'figure'),
        Output('mp', 'children'), # no idea why it needs 'children'...
        Output('me', 'children'), # no idea why it needs 'children'...
        Output('di', 'children'), # no idea why it needs 'children'...
        Output('ie', 'children'), # no idea why it needs 'children'...
        Input('term-button', 'value'),
        Input('interest-slider', 'value'),
        Input('loan-slider', 'value'),
        Input('extra-slider', 'value')
)
def modify_plot(term, ir, ls, es):

    df, ip = make_payment_table(ls, ir, term, es)
    default_end_date = df[df['Ending Balance'] == 0]['Payment Date'].min()
    extra_end_date   = df[df['Ending Balance w/ Extra'] == 0]['Payment Date'].min()
    
    melted = pd.melt(df, id_vars=['Payment Date'], value_vars=['Ending Balance', 
                                                              'Ending Balance w/ Extra'])
    
    fig = px.line(melted, x='Payment Date', y='value', color='variable', width=800, height=800)
    fig.add_vline(x=extra_end_date, line_dash='dot', line_color="black")
    fig.add_vrect(
        x0=extra_end_date,
        x1=default_end_date,
        fillcolor="green",
        opacity=0.2,
        annotation_position="top left",
        annotation_text="{0} Months Earlier endate".format((default_end_date - extra_end_date))
    )
    
    fig.update_layout(
        title="Mortgage Payment",
        xaxis_title="Payment Period (Months)",
        yaxis_title="Principal Remaining ($)",
        xaxis_range=[1,360],
        yaxis_range=[0,600000],
        legend=dict(
            title_text='Balance Variation',
            yanchor='bottom',
            y=0.05,
            xanchor='left',
            x=0.05)
    )

    default_interest = df["Interest"].sum()
    interest_saved   = df["Intereste"].sum()

    mp = f'Default Monthly Payment:      {locale.currency(round(ip,2), grouping = True)}'
    me = f'Monthly Payment w/ Extra:     {locale.currency(round(ip + es, 2), grouping = True)}'
    di = f'Default Total Interest Paid:  {locale.currency(round(default_interest, 2), grouping = True)}'
    ie = f'Total Interest Paid w/ Extra: {locale.currency(round(interest_saved, 2), grouping = True)}'

    return fig, mp, me, di, ie

if __name__ == '__main__':
    app.run_server(debug=True)
