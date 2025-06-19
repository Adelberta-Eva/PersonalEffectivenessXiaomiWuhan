import streamlit as st
import pandas as pd
import plotly.express as px

# 页面设置
st.set_page_config(page_title='汽车交付绩效分析', layout='wide')
st.title('🚗 汽车交付绩效分析平台')

# 上传 Excel
uploaded_file = st.file_uploader('👉 上传数据文件 (.xlsx)', type=['xlsx'])

# 确认按钮
if uploaded_file:
    st.success(f'📄 已上传文件： {uploaded_file.name}')
    if st.button('✅ 确认上传并开始分析'):

        # 读取数据
        df = pd.read_excel(uploaded_file, sheet_name='sheet')

        # 预处理
        df = df[['交付城市', '交付时间', '交付A岗', '订单ID', 'PDI OK→交付']].copy()
        df.columns = ['城市', '交付时间', 'A岗', '订单ID', 'PDI到交付']
        df['交付时间'] = pd.to_datetime(df['交付时间'])
        df['月份'] = df['交付时间'].dt.to_period('M').astype(str)
        df['周'] = df['交付时间'].dt.isocalendar().week
        df['日期'] = df['交付时间'].dt.date

        # 城市筛选
        city_options = df['城市'].unique().tolist()
        city = st.sidebar.selectbox('选择城市：', city_options)

        # 月份筛选
        month_options = df[df['城市'] == city]['月份'].unique().tolist()
        month = st.sidebar.selectbox('选择月份：', month_options)

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            '📊 城市&个人绩效',
            '🐢 最慢交付分析',
            '📈 周/日趋势',
            '💪 个人贡献占比'
        ])

        with tab1:
            st.header(f'{city} - 平均PDI到交付时间')

            city_avg = df[(df['城市'] == city) & (df['月份'] == month)]['PDI到交付'].mean()
            st.metric(label=f'{city}整体平均 (天)', value=f'{city_avg:.2f}')

            personal_avg = df[(df['城市'] == city) & (df['月份'] == month)].groupby('A岗')['PDI到交付'].mean().sort_values()
            fig = px.bar(personal_avg, orientation='h', title='个人平均PDI到交付', labels={'value':'平均(天)', 'index':'A岗'}, text_auto='.2f')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.header(f'{city} - 最慢交付分析')

            n_slowest = st.slider('选择最慢N单 (5~30)', min_value=5, max_value=30, value=10)
            slowest_df = df[(df['城市'] == city) & (df['月份'] == month)].sort_values(by='PDI到交付', ascending=False).head(n_slowest)
            st.subheader('最慢 N 单')
            st.dataframe(slowest_df[['订单ID', '交付时间', 'A岗', 'PDI到交付']])

            person = st.selectbox('选择A岗：', df[df['城市'] == city]['A岗'].unique().tolist())
            person_df = df[(df['城市'] == city) & (df['A岗'] == person) & (df['月份'] == month)].sort_values(by='PDI到交付', ascending=False).head(5)
            st.subheader(f'{person} 最慢5单')
            st.dataframe(person_df[['订单ID', '交付时间', 'PDI到交付']])

        with tab3:
            st.header(f'{city} - 趋势分析')

            trend_type = st.radio('趋势类型', ['按周', '按日'], horizontal=True)

            if trend_type == '按周':
                df_week = df[(df['城市'] == city) & (df['月份'] == month)].groupby('周').size().reset_index(name='交付数量')
                fig_week = px.line(df_week, x='周', y='交付数量', markers=True, title='按周交付趋势')
                st.plotly_chart(fig_week, use_container_width=True)
                st.dataframe(df_week)

            else:
                df_day = df[(df['城市'] == city) & (df['月份'] == month)].groupby('日期').size().reset_index(name='交付数量')
                fig_day = px.line(df_day, x='日期', y='交付数量', markers=True, title='按日交付趋势')
                st.plotly_chart(fig_day, use_container_width=True)
                st.dataframe(df_day)

        with tab4:
            st.header(f'{city} - 个人贡献占比')

            contrib_type = st.radio('选择粒度', ['按日', '按周', '按月'], horizontal=True)

            if contrib_type == '按日':
                total_day = df[(df['城市'] == city) & (df['月份'] == month)].groupby('日期').size().reset_index(name='总交付')
                df_c = df[(df['城市'] == city) & (df['月份'] == month)].groupby(['日期', 'A岗']).size().reset_index(name='交付数量')
                df_c = pd.merge(df_c, total_day, on='日期')
                df_c['占比(%)'] = df_c['交付数量'] / df_c['总交付'] * 100
                selected_day = st.selectbox('选择日期查看：', df_c['日期'].unique())
                df_show = df_c[df_c['日期'] == selected_day].sort_values(by='占比(%)', ascending=False)

            elif contrib_type == '按周':
                total_week = df[(df['城市'] == city) & (df['月份'] == month)].groupby('周').size().reset_index(name='总交付')
                df_c = df[(df['城市'] == city) & (df['月份'] == month)].groupby(['周', 'A岗']).size().reset_index(name='交付数量')
                df_c = pd.merge(df_c, total_week, on='周')
                df_c['占比(%)'] = df_c['交付数量'] / df_c['总交付'] * 100
                selected_week = st.selectbox('选择周查看：', df_c['周'].unique())
                df_show = df_c[df_c['周'] == selected_week].sort_values(by='占比(%)', ascending=False)

            else:
                total_month = df[df['城市'] == city].groupby('月份').size().reset_index(name='总交付')
                df_c = df[df['城市'] == city].groupby(['月份', 'A岗']).size().reset_index(name='交付数量')
                df_c = pd.merge(df_c, total_month, on='月份')
                df_c['占比(%)'] = df_c['交付数量'] / df_c['总交付'] * 100
                selected_month = st.selectbox('选择月份查看：', df_c['月份'].unique())
                df_show = df_c[df_c['月份'] == selected_month].sort_values(by='占比(%)', ascending=False)

            fig_contrib = px.bar(df_show, x='A岗', y='占比(%)', text_auto='.1f', title='个人贡献占比')
            st.plotly_chart(fig_contrib, use_container_width=True)
            st.dataframe(df_show[['A岗', '交付数量', '占比(%)']])
