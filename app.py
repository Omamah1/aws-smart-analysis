import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="لوحة تحكم المستندات الذكية",
    page_icon="📊",
    layout="wide"
)

# 2. تصميم واجهة المستخدم باستخدام CSS بسيط
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .invoice-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        border-right: 5px solid #007bff; 
        margin-bottom: 20px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. عنوان التطبيق
st.title("📊 نظام تحليل الفواتير الذكي - AWS")
st.markdown("---")

# 4. رابط الـ API الخاص بك (تأكد من وضع رابطك هنا)
API_URL = "https://n7393xuxra.execute-api.eu-west-1.amazonaws.com"

# 5. القائمة الجانبية (Sidebar)
st.sidebar.header("⚙️ لوحة التحكم")
st.sidebar.info("هذا التطبيق متصل بـ AWS عبر تقنية Serverless")

if st.sidebar.button("تحديث البيانات 🔄", use_container_width=True):
    with st.spinner('جاري جلب البيانات من السحابة...'):
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                data = response.json()
                
                if not data or len(data) == 0:
                    st.warning("⚠️ لا توجد بيانات في الجدول حالياً. ارفع ملفات في S3 أولاً.")
                else:
                    # تحويل البيانات إلى Pandas DataFrame
                    df = pd.DataFrame(data)

                    # --- قسم الإحصائيات العلوي ---
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("إجمالي المستندات", len(df))
                    with col_m2:
                        pos_count = len(df[df['Sentiment'] == 'POSITIVE']) if 'Sentiment' in df.columns else 0
                        st.metric("نتائج إيجابية ✅", pos_count)
                    with col_m3:
                        neg_count = len(df[df['Sentiment'] == 'NEGATIVE']) if 'Sentiment' in df.columns else 0
                        st.metric("نتائج تحتاج مراجعة ❌", neg_count)

                    st.markdown("### 📈 التحليل المرئي")
                    
                    # --- قسم الرسوم البيانية ---
                    col_g1, col_g2 = st.columns([2, 1])
                    with col_g1:
                        if 'Sentiment' in df.columns:
                            fig_pie = px.pie(df, names='Sentiment', title='توزيع تحليل المشاعر', 
                                            color_discrete_sequence=px.colors.qualitative.Set3)
                            st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col_g2:
                        st.info("""
                        **💡 ملاحظة حول التكلفة:**
                        هذا الاستعلام استهلك طلب (Request) واحد فقط من Lambda، وهو ضمن النطاق المجاني لـ AWS.
                        """)

                    st.markdown("---")
                    st.markdown("### 📄 تفاصيل السجلات المستخرجة")

                    # --- عرض البيانات كبطاقات مع معالجة الأخطاء ---
                    for index, row in df.iterrows():
                        # تحويل كل القيم لنصوص لتجنب خطأ float is not subscriptable
                        inv_id = str(row.get('InvoiceId', 'N/A'))
                        sentiment = str(row.get('Sentiment', 'Unknown'))
                        raw_text = str(row.get('RawText', 'لا يوجد نص مستخرج'))
                        
                        st.markdown(f"""
                        <div class="invoice-card">
                            <h4 style="color: #007bff;">📄 سجل: {inv_id}</h4>
                            <p><b>حالة المشاعر:</b> {sentiment}</p>
                            <hr style="border: 0.5px solid #eee;">
                            <p><b>النص الذي تم التعرف عليه:</b></p>
                            <div style="background: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 0.9em;">
                                {raw_text[:500]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error(f"❌ خطأ في الاتصال: {response.status_code}")
        except Exception as e:
            st.error(f"⚠️ حدث خطأ أثناء عرض البيانات: {str(e)}")

# تذييل الصفحة في القائمة الجانبية
st.sidebar.markdown("---")
st.sidebar.caption("بنية المشروع: S3 -> Textract -> Comprehend -> DynamoDB -> API Gateway -> Streamlit")