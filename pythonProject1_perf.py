import streamlit as st
import pandas as pd
import plotly.express as px

# 页面标题
st.title('🚗 汽车交付绩效分析平台')

# 上传 Excel
uploaded_file = st.file_uploader('📤 上传交付数据文件 (Excel)', type=['xlsx'])

# 开始分析
if uploaded_file:
    st.success(f'📄 已上传文件： {uploaded_file.name}')

    if st.button('✅ 确认上传并开始分析'):
        with st.spinner('🔄 正在加载数据并分析中，请稍等...'):

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
            city = st.selectbox('选择城市：', city_options)

            # 月份筛选
            month_options = df[df['城市'] == city]['月份'].unique().tolist()
            month = st.selectbox('选择月份：', month_options)

            # tabs 功能
            tab1, tab2, tab3 = st.tabs(['1. 城市&个人绩效', '2. 最慢交付分析', '3. 周/日趋势&个人贡献'])

            with tab1:
                st.header(f'{city} - 平均PDI到交付时间')
                city_avg = df[(df['城市'] == city) & (df['月份'] == month)]['PDI到交付'].mean()
                st.metric(label=f'{city}整体平均 (天)', value=f'{city_avg:.2f}')

                personal_avg = df[(df['城市'] == city) & (df['月份'] == month)].groupby('A岗')[
                    'PDI到交付'].mean().sort_values()
                fig1 = px.bar(personal_avg, x=personal_avg.index, y=personal_avg.values,
                              labels={'x': 'A岗', 'y': '平均PDI到交付（天）'},
                              text_auto='.2f')
                st.plotly_chart(fig1, use_container_width=True)

            with tab2:
                st.header(f'{city} - 最慢交付分析 ({month})')
                n_slowest = st.slider('选择最慢N单', min_value=5, max_value=30, value=10, step=1)

                slowest_orders = df[(df['城市'] == city) & (df['月份'] == month)].sort_values(by='PDI到交付',
                                                                                              ascending=False).head(
                    n_slowest)
                st.dataframe(slowest_orders[['订单ID', '交付时间', 'A岗', 'PDI到交付']])

                person = st.selectbox('选择A岗查看个人最慢5单', df[(df['城市'] == city)]['A岗'].unique().tolist())
                person_df = df[(df['城市'] == city) & (df['A岗'] == person) & (df['月份'] == month)].sort_values(
                    by='PDI到交付', ascending=False)
                st.dataframe(person_df[['订单ID', '交付时间', 'PDI到交付']].head(5))

            with tab3:
                st.header(f'{city} - 趋势&个人贡献 ({month})')

                trend_type = st.radio('选择趋势类型', ['周趋势', '日趋势'])

                if trend_type == '周趋势':
                    df_week = df[(df['城市'] == city) & (df['月份'] == month)].groupby('周').size().reset_index(
                        name='交付数量')
                    fig_week = px.line(df_week, x='周', y='交付数量', markers=True)
                    st.plotly_chart(fig_week, use_container_width=True)
                else:
                    df_day = df[(df['城市'] == city) & (df['月份'] == month)].groupby('日期').size().reset_index(
                        name='交付数量')
                    fig_day = px.line(df_day, x='日期', y='交付数量', markers=True)
                    st.plotly_chart(fig_day, use_container_width=True)

                # 个人贡献占比
                st.subheader('📊 个人贡献交付占比')

                contrib_type = st.radio('粒度选择', ['按日', '按周', '按月'])

                if contrib_type == '按日':
                    group_field = '日期'
                elif contrib_type == '按周':
                    group_field = '周'
                else:
                    group_field = '月份'

                df_contrib = df[df['城市'] == city].groupby([group_field, 'A岗']).size().reset_index(name='交付数量')

                if group_field == '日期':
                    options = df_contrib['日期'].unique().tolist()
                elif group_field == '周':
                    options = df_contrib['周'].unique().tolist()
                else:
                    options = df_contrib['月份'].unique().tolist()

                selected_period = st.selectbox('选择周期查看', options)

                df_sel = df_contrib[df_contrib[group_field] == selected_period]
                total_num = df_sel['交付数量'].sum()
                df_sel['占比(%)'] = df_sel['交付数量'] / total_num * 100

                fig_contrib = px.bar(df_sel, x='A岗', y='占比(%)', text_auto='.1f')
                st.plotly_chart(fig_contrib, use_container_width=True)

