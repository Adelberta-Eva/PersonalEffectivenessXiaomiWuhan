import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='汽车交付绩效分析平台', layout='wide')

st.title('🚗 汽车交付绩效分析平台')

# 上传 Excel
uploaded_file = st.file_uploader('📤 上传交付数据文件 (Excel)', type=['xlsx'])

# 用 session_state 存 df
if 'df' not in st.session_state:
    st.session_state.df = None

# 上传并确认按钮
if uploaded_file:
    st.success(f'📄 已上传文件： {uploaded_file.name}')

    if st.button('✅ 确认上传并开始分析'):
        with st.spinner('🔄 正在加载数据并分析中，请稍等...'):
            df = pd.read_excel(uploaded_file, sheet_name='sheet')
            df = df[['交付城市', '交付时间', '交付A岗', '订单ID', 'PDI OK→交付']].copy()
            df.columns = ['城市', '交付时间', 'A岗', '订单ID', 'PDI到交付']
            df['交付时间'] = pd.to_datetime(df['交付时间'])
            df['月份'] = df['交付时间'].dt.to_period('M').astype(str)
            df['周'] = df['交付时间'].dt.isocalendar().week
            df['日期'] = df['交付时间'].dt.date

            # 存到 session_state
            st.session_state.df = df
            st.success('✅ 数据加载完成，您可以自由切换页面浏览！')

# 如果 df 已有，才显示 tabs 界面
if st.session_state.df is not None:
    df = st.session_state.df

    city_options = df['城市'].unique().tolist()
    city = st.selectbox('选择城市：', city_options)

    month_options = df[df['城市'] == city]['月份'].unique().tolist()
    month = st.selectbox('选择月份：', month_options)

    tab1, tab2, tab3 = st.tabs(['1. 城市&个人绩效', '2. 最慢交付分析', '3. 周/日趋势&个人贡献'])

    # tab1
    with tab1:
        st.header(f'{city} - 平均PDI到交付时间')

        city_avg = df[(df['城市'] == city) & (df['月份'] == month)]['PDI到交付'].mean()
        st.metric(label=f'{city}整体平均 (天)', value=f'{city_avg:.2f}')

        personal_avg = df[(df['城市'] == city) & (df['月份'] == month)].groupby('A岗')['PDI到交付'].mean().sort_values()
        fig1 = px.bar(personal_avg, x=personal_avg.index, y=personal_avg.values, text_auto='.1f',
                      labels={'x': 'A岗', 'y': '平均天数'})
        st.plotly_chart(fig1, use_container_width=True)

    # tab2
    with tab2:
        st.header(f'{city} - 最慢交付分析 ({month})')

        max_n = st.slider('选择最慢N单 (含订单ID / 交付时间)', min_value=5, max_value=30, value=10)

        slowest_df = df[(df['城市'] == city) & (df['月份'] == month)].sort_values(by='PDI到交付', ascending=False).head(
            max_n)
        st.dataframe(slowest_df[['订单ID', '交付时间', 'A岗', 'PDI到交付']])

        person = st.selectbox('选择A岗查看个人最慢5单：',
                              df[(df['城市'] == city) & (df['月份'] == month)]['A岗'].unique().tolist())
        person_df = df[(df['城市'] == city) & (df['月份'] == month) & (df['A岗'] == person)].sort_values(by='PDI到交付',
                                                                                                         ascending=False).head(
            5)
        st.dataframe(person_df[['订单ID', '交付时间', 'PDI到交付']])

    # tab3
    with tab3:
        st.header(f'{city} - 趋势 & 个人贡献 ({month})')

        view_mode = st.radio('查看模式：', ['按周趋势', '按日趋势'])

        if view_mode == '按周趋势':
            df_week = df[(df['城市'] == city) & (df['月份'] == month)].groupby('周').size().reset_index(name='交付数量')
            fig2 = px.line(df_week, x='周', y='交付数量', markers=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df_week)

        else:
            df_day = df[(df['城市'] == city) & (df['月份'] == month)].groupby('日期').size().reset_index(
                name='交付数量')
            fig3 = px.line(df_day, x='日期', y='交付数量', markers=True)
            st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(df_day)

        st.markdown('---')
        st.subheader('个人贡献 - 交付数量占比')

        contrib_mode = st.radio('贡献查看维度：', ['按天', '按周', '按月'])

        if contrib_mode == '按天':
            contrib_day = df[(df['城市'] == city) & (df['月份'] == month)].groupby(['日期', 'A岗']).size().reset_index(
                name='交付数量')
            total_day = contrib_day.groupby('日期')['交付数量'].sum().reset_index(name='总交付')
            contrib_day = pd.merge(contrib_day, total_day, on='日期')
            contrib_day['占比(%)'] = contrib_day['交付数量'] / contrib_day['总交付'] * 100
            selected_day = st.selectbox('选择日期查看个人贡献：', contrib_day['日期'].unique())
            df_day_view = contrib_day[contrib_day['日期'] == selected_day].sort_values(by='占比(%)', ascending=False)
            fig_c1 = px.bar(df_day_view, x='A岗', y='占比(%)', text_auto='.1f')
            st.plotly_chart(fig_c1, use_container_width=True)

        elif contrib_mode == '按周':
            contrib_week = df[(df['城市'] == city) & (df['月份'] == month)].groupby(['周', 'A岗']).size().reset_index(
                name='交付数量')
            total_week = contrib_week.groupby('周')['交付数量'].sum().reset_index(name='总交付')
            contrib_week = pd.merge(contrib_week, total_week, on='周')
            contrib_week['占比(%)'] = contrib_week['交付数量'] / contrib_week['总交付'] * 100
            selected_week = st.selectbox('选择周查看个人贡献：', contrib_week['周'].unique())
            df_week_view = contrib_week[contrib_week['周'] == selected_week].sort_values(by='占比(%)', ascending=False)
            fig_c2 = px.bar(df_week_view, x='A岗', y='占比(%)', text_auto='.1f')
            st.plotly_chart(fig_c2, use_container_width=True)

        else:
            contrib_month = df[(df['城市'] == city) & (df['月份'] == month)].groupby(['A岗']).size().reset_index(
                name='交付数量')
            total_month = contrib_month['交付数量'].sum()
            contrib_month['占比(%)'] = contrib_month['交付数量'] / total_month * 100
            df_month_view = contrib_month.sort_values(by='占比(%)', ascending=False)
            fig_c3 = px.bar(df_month_view, x='A岗', y='占比(%)', text_auto='.1f')
            st.plotly_chart(fig_c3, use_container_width=True)
