import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import boto3
from botocore.exceptions import NoCredentialsError

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="نظام تحليل المستندات الذكي",
    page_icon="🔍",
    layout="wide"
)

# 2. استدعاء الإعدادات من Secrets (للأمان)
# تأكد من إضافة هذه القيم في إعدادات Streamlit Cloud Secrets
try:
    S3_BUCKET_NAME = st.secrets["S3_BUCKET"]
    AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY"]
    AWS_SECRET_KEY = st.secrets["AWS_SECRET_KEY"]
    AWS_REGION = st.secrets["AWS_REGION"]
    API_URL = st.secrets["API_URL"] # رابط الـ API Gateway
except Exception as e:
    st.error("⚠️ لم يتم العثور على الإعدادات السرية (Secrets). تأكد من إضافتها في Streamlit Cloud.")
    st.stop()

# 3. دالة رفع الملفات إلى S3
def upload_to_s3(file_data, file_name):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=file_data)
        return True
    except Exception as e:
        st.error(f"❌ فشل الرفع إلى S3: {e}")
        return False

# 4. تصميم الواجهة (CSS)
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .invoice-card { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border-right: 5px solid #007bff; margin-bottom: 20px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

# 5. القائمة الجانبية (Sidebar) - للرفع والتحكم
st.sidebar.header("📤 رفع مستند جديد")
uploaded_file = st.sidebar.file_uploader("اختر صورة فاتورة أو مستند", type=['png', 'jpg', 'jpeg'])

if st.sidebar.button("بدء المعالجة الذكية 🚀", use_container_width=True):
    if uploaded_file is not None:
        with st.spinner('جاري رفع الملف إلى S3 وتحفيز الذكاء الاصطناعي...'):
            if upload_to_s3(uploaded_file.getvalue(), uploaded_file.name):
                st.sidebar.success(f"✅ تم الرفع بنجاح: {uploaded_file.name}")
                st.sidebar.info("انتظر ثوانٍ قليلة للمعالجة ثم اضغط على 'تحديث البيانات' بالأسفل.")
    else:
        st.sidebar.warning("⚠️ الرجاء اختيار ملف أولاً.")

st.sidebar.markdown("---")
refresh_btn = st.sidebar.button("تحديث البيانات 🔄", use_container_width=True)

# 6. الجزء الرئيسي من الواجهة (لوحة التحكم)
st.title("📊 لوحة تحكم المستندات الذكية (Serverless)")
st.markdown(f"المستودع السحابي الحالي: `{S3_BUCKET_NAME}`")

# جلب البيانات عند الضغط على تحديث أو عند فتح الصفحة
if refresh_btn or 'first_run' not in st.session_state:
    st.session_state['first_run'] = True
    with st.spinner('جاري جلب البيانات من DynamoDB...'):
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    st.info("📭 لا توجد بيانات معالجة حالياً. ابدأ برفع ملف من القائمة الجانبية.")
                else:
                    df = pd.DataFrame(data)
                    
                    # الإحصائيات السريعة
                    m1, m2, m3 = st.columns(3)
                    m1.metric("إجمالي المستندات", len(df))
                    pos_count = len(df[df['Sentiment'] == 'POSITIVE']) if 'Sentiment' in df.columns else 0
                    m2.metric("إيجابي ✅", pos_count)
                    neg_count = len(df[df['Sentiment'] == 'NEGATIVE']) if 'Sentiment' in df.columns else 0
                    m3.metric("مراجعة ❌", neg_count)

                    # الرسوم البيانية
                    st.markdown("### 📈 تحليل المشاعر")
                    if 'Sentiment' in df.columns:
                        fig = px.pie(df, names='Sentiment', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig, use_container_width=True)

                    # عرض السجلات
                    st.markdown("### 📄 السجلات الأخيرة")
                    for _, row in df.iterrows():
                        inv_id = str(row.get('InvoiceId', 'N/A'))
                        sentiment = str(row.get('Sentiment', 'Unknown'))
                        raw_text = str(row.get('RawText', 'لا يوجد نص مستخرج'))
                        
                        st.markdown(f"""
                        <div class="invoice-card">
                            <h4 style="color: #007bff;">ID: {inv_id}</h4>
                            <p><b>تحليل المشاعر:</b> {sentiment}</p>
                            <p style="font-size: 0.85em; background: #f0f2f6; padding: 10px; border-radius: 5px;">
                                {raw_text[:300]}...
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("❌ تعذر الاتصال بـ API Gateway.")
        except Exception as e:
            st.error(f"⚠️ حدث خطأ: {e}")

st.sidebar.caption("بنية المشروع: S3 ➔ Lambda ➔ Textract ➔ DynamoDB ➔ API Gateway ➔ Streamlit")