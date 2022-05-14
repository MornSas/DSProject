import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
import geopandas as gpd
import plotly.express as px
from pandas import DataFrame
from pandas.io.parsers import TextFileReader

with st.echo(code_location='below'):
    """
    ## Hello, Happy World!
    """


    def print_hello(name="World"):
        st.write(f"### Hello, {name}! Hope you are happy too!")


    name = st.text_input("Your name", key="name", value="Anonymous")
    print_hello(name)


    @st.cache(allow_output_mutation=True)
    def get_data(path):
        return pd.read_csv(path)


    df = get_data('https://raw.githubusercontent.com/MornSas/DSProject/master/world-happiness-report.csv')
    df.rename(columns={'Life Ladder': 'Ladder score'}, inplace=True)
    df2 = get_data('https://raw.githubusercontent.com/MornSas/DSProject/master/world-happiness-report-2021.csv')

    """
    ## Выберите страну из списка, чтобы посмотреть данные об уровне счастья за 2021 год
    """

    country = st.selectbox(
        "Country", df2.sort_values('Country name')['Country name']
    )

    df_selection = df2[lambda x: x["Country name"] == country]
    df_selection

    """
    ## Изменения уровня счастья
    """

    df_selection1 = df[lambda x: x["Country name"] == country]
    chart = (
        alt.Chart(df_selection1)
            .mark_circle()
            .encode(x=alt.X("year", scale=alt.Scale(domain=(df['year'].min(), df['year'].max()))), y="Ladder score",
                    tooltip="Ladder score")
            .properties(
            width=600,
            height=300
        )
    )
    st.altair_chart(
        (
                chart + chart.transform_loess('year', 'Ladder score').mark_line()
        ).interactive()
    )

    """
    ## Посмотрим на 10 самых счастливых и несчастных стран
    """

    top = df2.groupby('Country name')['Ladder score'].mean().sort_values(ascending=False)[:10]
    bot = df2.groupby('Country name')['Ladder score'].mean().sort_values(ascending=True)[:10]
    top_to_bot = top.append(bot).sort_values(ascending=False)
    x = list(top_to_bot.keys()[:10])
    y = [top_to_bot[i] for i in range(10)]
    x1 = list(top_to_bot.keys()[10:])
    y1 = [top_to_bot[i] for i in range(10, 20)]
    fig = plt.figure()
    fig.set_figwidth(7.5)
    fig.set_figheight(7.5)
    ax1 = fig.add_subplot(111)
    ax1.set_ylabel('Country name')
    ax1.set_xlabel('Ladder score')
    ax1.set_title('10 Best and 10 Worst')
    for i, v in enumerate(y):
        ax1.text(v, i, str(v), color='green', fontweight='bold')
    for i, v in enumerate(y1):
        ax1.text(v, i + 10, str(v), color='red', fontweight='bold')
    plt.barh(x, y, color='green')
    plt.barh(x1, y1, color='red')
    st.pyplot(fig)

    '''
    ## Выберите параметр, чтобы увидеть его соответствие значению уровня счастья и регрессию
    '''

    factor = st.selectbox(
        "Factor", ['Logged GDP per capita', 'Social support', 'Healthy life expectancy',
                   'Freedom to make life choices', 'Generosity', 'Perceptions of corruption']
    )

    chart1 = (alt.Chart(df2).mark_circle().encode(
        alt.X(factor, scale=alt.Scale(domain=(df2[factor].min(), df2[factor].max()))),
        alt.Y('Ladder score', scale=alt.Scale(domain=(2, 9))),
        alt.Color('Regional indicator'),
        tooltip=[alt.Tooltip('Country name'),
                 alt.Tooltip('Ladder score'),
                 alt.Tooltip(factor)]
    ).properties(
        width=800,
        height=500
    ))
    st.altair_chart(chart1.interactive())

    fig_1 = plt.figure(figsize=(10, 10))
    reg = sns.jointplot(data=df2, x=factor, y='Ladder score', kind='reg')
    st.pyplot(reg)

    '''
    ## Как этот фактор менялся до 2021 года
    '''
    if factor == 'Logged GDP per capita':
        factor = 'Log GDP per capita'
    elif factor == 'Healthy life expectancy':
        factor = 'Healthy life expectancy at birth'

    anifig = px.scatter(df.sort_values('year').reset_index(drop=True), x=factor, y='Ladder score', animation_frame='year',
                        animation_group='Country name',
                        hover_name='Country name', range_x=[df[factor].min(), df[factor].max()], range_y=[1, 9]
                        )
    st.plotly_chart(anifig)

    '''
    ## Изменения по стране, выбранной выше
    '''

    df_country = df[df['Country name'] == country]
    anicountry = px.scatter(df_country.sort_values('year').reset_index(drop=True), x=factor, y='Ladder score',
                        animation_group='Country name',
                        animation_frame='year',
                        hover_name='Country name', range_x=[df[factor].min(), df[factor].max()], range_y=[1, 9],
                        color='Country name'
                        )
    st.plotly_chart(anicountry)


    '''
    ## Как уровень счастья выглядит на карте мира
    '''

    ###FROM:(https://www.relataly.com/visualize-covid-19-data-on-a-geographic-heat-maps/291/)
    # Setting the path to the shapefile
    SHAPEFILE = '/vsicurl/https://github.com/MornSas/DSProject/blob/master/ne_10m_admin_0_countries.shp?raw=true'

    # Read shapefile using Geopandas
    geo_df = gpd.read_file(SHAPEFILE)[['ADMIN', 'ADM0_A3', 'geometry']]

    # Rename columns.
    geo_df.columns = ['country', 'country_code', 'geometry']

    # Drop row for 'Antarctica'. It takes a lot of space in the map and is not of much use
    geo_df = geo_df.drop(geo_df.loc[geo_df['country'] == 'Antarctica'].index)

    ###END FROM

    d = {'United Republic of Tanzania': 'Tanzania', 'Czechia': 'Czech Republic', 'Republic of Serbia': 'Serbia',
         'United States of America': 'United States', 'Hong Kong S.A.R.': 'Hong Kong S.A.R. of China',
         'Taiwan': 'Taiwan Province of China', 'Palestine': 'Palestinian Territories',
         'Republic of the Congo': 'Congo (Brazzaville)', 'Greenland': 'Denmark'}
    geo_df = geo_df.replace({'country': d})
    df_map = pd.merge(geo_df, df2, how='left', left_on='country', right_on='Country name').fillna(1)
    color = 'RdYlGn'
    col = df_map['Ladder score']
    df_data = df_map[col > 1]
    df_nodata = df_map[col == 1]
    fig_map, ax_map = plt.subplots(figsize=(24, 12))
    ax_map.axis = "off"
    df_data.plot(column=df_data['Ladder score'], ax=ax_map, edgecolor='black', linewidth=1, cmap=color, legend=True)
    df_nodata.plot(column=df_nodata['Ladder score'], ax=ax_map, edgecolor='black', linewidth=1, color='white')
    ax_map.set_title('Level of Happiness')
    st.pyplot(fig_map)
