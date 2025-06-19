import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="交付绩效分析平台", layout="wide")

st.title('🚗 汽车交付绩效分析平台（上传数据版）')

uploaded_file = st.file_uploader("📂 请上传数据源 Excel 文件（字段格式与模板一致）：", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='sheet')

        # 字段处理
        df = df[['交付城市', '交付时间', '交付A岗', '订单ID', '车架号', 'PDI OK→交付']].copy()
        df.columns = ['城市', '交付时间', 'A岗', '订单ID', '车架号', 'PDI到交付']
        df['交付时间'] = pd.to_datetime(df['交付时间'])
        df['月份'] = df['交付时间'].dt.to_period('M').astype(str)
        df['周'] = df['交付时间'].dt.isocalendar().week
        df['日期'] = df['交付时间'].dt.date

        # 城市、月份选择
        col1, col2 = st.columns(2)
        with col1:
            city = st.selectbox('🏙️ 选择城市：', df['城市'].unique())
        with col2:
            month = st.selectbox('🗓️ 选择月份：', df[df['城市'] == city]['月份'].unique())

        # 页面模块
        tab1, tab2, tab3, tab4 = st.tabs(['城市绩效', '最慢交付分析', '趋势图', '贡献占比'])

        with tab1:
            st.header(f'{city} - 平均 PDI 到交付时间')

            city_df = df[(df['城市'] == city) & (df['月份'] == month)]
            city_avg = city_df['PDI到交付'].mean()
            st.metric(f'{city} 平均 (天)', f'{city_avg:.2f}')

            personal_avg = city_df.groupby('A岗')['PDI到交付'].mean().sort_values()
            fig1 = px.bar(personal_avg, x=personal_avg.index, y=personal_avg.values,
                          labels={"x": "A岗", "y": "平均交付天数"}, text_auto='.2f')
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            st.header(f'{city} - 最慢交付分析')

            # 选择最慢单数量
            top_n = st.slider('显示最慢 N 单（含订单ID/车架/时间）：', 5, 30, 10)

            slow_df = df[(df['城市'] == city) & (df['月份'] == month)]
            slow_df_sorted = slow_df.sort_values(by='PDI到交付', ascending=False)

            st.subheader(f'📊 {city} 最慢 {top_n} 单')
            st.dataframe(slow_df_sorted[['A岗', '订单ID', '车架号', '交付时间', 'PDI到交付']].head(top_n))

            person = st.selectbox('选择 A岗 查看其最慢交付记录：', slow_df['A岗'].unique())
            person_df = slow_df[slow_df['A岗'] == person].sort_values(by='PDI到交付', ascending=False)

            st.subheader(f'{person} 最慢 5 单')
            st.dataframe(person_df[['订单ID', '车架号', '交付时间', 'PDI到交付']].head(5))

        with tab3:
            st.header(f'{city} - 交付趋势分析')
            trend_mode = st.radio('选择趋势维度：', ['按周趋势', '按日趋势'])

            df_trend = df[(df['城市'] == city) & (df['月份'] == month)]

            if trend_mode == '按周趋势':
                week_data = df_trend.groupby('周').size().reset_index(name='交付数量')
                fig = px.line(week_data, x='周', y='交付数量', markers=True, title=f"{city} 每周交付数量")
            else:
                day_data = df_trend.groupby('日期').size().reset_index(name='交付数量')
                fig = px.line(day_data, x='日期', y='交付数量', markers=True, title=f"{city} 每日交付数量")

            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.header(f'{city} - 个人交付贡献占比')

            mode = st.radio("选择时间维度：", ['按日', '按周', '按月'])

            df_c = df[df['城市'] == city]

            if mode == '按日':
                day_count = df_c.groupby(['日期', 'A岗']).size().reset_index(name='交付数量')
                total_day = df_c.groupby('日期').size().reset_index(name='总交付')
                df_c = pd.merge(day_count, total_day, on='日期')
                df_c['占比(%)'] = df_c['交付数量'] / df_c['总交付'] * 100

                selected_day = st.selectbox('选择日期查看个人贡献：', sorted(df_c['日期'].unique(), reverse=True))
                df_day = df_c[df_c['日期'] == selected_day].sort_values(by='占比(%)', ascending=False)

                fig_contrib = px.bar(df_day, x='A岗', y='占比(%)', text_auto='.1f', title=f'{selected_day} 个人交付占比')
                st.plotly_chart(fig_contrib, use_container_width=True)

            elif mode == '按周':
                week_count = df_c.groupby(['周', 'A岗']).size().reset_index(name='交付数量')
                total_week = df_c.groupby('周').size().reset_index(name='总交付')
                df_c = pd.merge(week_count, total_week, on='周')
                df_c['占比(%)'] = df_c['交付数量'] / df_c['总交付'] * 100

                selected_week = st.selectbox('选择周查看贡献：', sorted(df_c['周'].unique(), reverse=True))
                df_week = df_c[df_c['周'] == selected_week].sort_values(by='占比(%)', ascending=False)

                fig_contrib = px.bar(df_week, x='A岗', y='占比(%)', text_auto='.1f', title=f'第{selected_week}周 个人交付占比')
                st.plotly_chart(fig_contrib, use_container_width=True)

            else:  # 按月
                month_count = df_c.groupby(['月份', 'A岗']).size().reset_index(name='交付数量')
                total_month = df_c.groupby('月份').size().reset_index(name='总交付')
                df_c = pd.merge(month_count, total_month, on='月份')
                df_c['占比(%)'] = df_c['交付数量'] / df_c['总交付'] * 100

                selected_month = st.selectbox('选择月份查看贡献：', sorted(df_c['月份'].unique(), reverse=True))
                df_month = df_c[df_c['月份'] == selected_month].sort_values(by='占比(%)', ascending=False)

                fig_contrib = px.bar(df_month, x='A岗', y='占比(%)', text_auto='.1f', title=f'{selected_month} 个人交付占比')
                st.plotly_chart(fig_contrib, use_container_width=True)

    except Exception as e:
        st.error(f"❌ 数据加载失败，请检查 Excel 文件格式是否正确。\n错误信息：{e}")
else:
    st.info("👆 请上传一份 Excel 数据源开始分析")
