from nicegui import ui
import requests
import io
import re
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

API_BASE = "http://127.0.0.1:8000/api"

def call_api(endpoint, method="get", payload=None, params=None):
    try:
        url = f"{API_BASE}{endpoint}"
        if method.lower() == "get":
            r = requests.get(url, params=params, timeout=15)
        else:
            r = requests.post(url, json=payload, timeout=30)
        
        if r.status_code == 200:
            return r.json()
        ui.notify(f"❌ Error {r.status_code}: {r.text}", color="red")
    except Exception as e:
        ui.notify(f"⚠️ API Call Exception: {e}", color="red")
    return None


@ui.page('/')
def main_page():
    with ui.column().classes('w-full items-center p-8 bg-gray-50 min-h-screen'):
        ui.label("🔍 Business Intelligence Pro").classes('text-4xl font-bold text-blue-700 mb-2')
        ui.label("Strategic Company Analysis & Due Diligence").classes('text-lg text-gray-600 mb-8')

        with ui.card().classes('w-2/3 p-6 space-y-4 shadow-md bg-white'):
            company_input = ui.input(
                label='🎯 Company Name', 
                placeholder='e.g. Caprae Capital Partners, OpenAI, Stripe'
            ).classes('w-full')
            
            url_input = ui.input(
                label='🔗 Company Website (optional)', 
                placeholder='https://www.capraecapital.com/'
            ).classes('w-full')
            
            strategic_toggle = ui.checkbox(
                'Include strategic market research', 
                value=False
            ).classes('w-full text-sm text-gray-600')
            
            ui.label("Get deeper competitive and market context").classes('text-xs text-gray-500 -mt-2 mb-2')
            
            result_area = ui.column().classes('w-full mt-6 space-y-4')
            analysis_progress = ui.linear_progress(show_value=False).classes('w-full hidden')

            last_insights = {}

            def generate_action():
                if not company_input.value.strip():
                    ui.notify("Please enter a company name.", color="orange")
                    return

                analysis_progress.set_visibility(True)
                ui.notify("🔍 Conducting business research...", color="blue")
                
                website_input = url_input.value.strip()
                enrich_payload = {
                    "company_name": company_input.value.strip(),
                    "company_url": website_input if website_input else ""
                }
                
                enrich_data = call_api("/enrich/", method="post", payload=enrich_payload)
                if not enrich_data or enrich_data.get('status') != 'success':
                    analysis_progress.set_visibility(False)
                    ui.notify("⚠️ Research failed - please verify company name.", color="red")
                    return

                enriched = enrich_data['data'][0]
                ui.notify("✨ Generating strategic analysis...", color="green")

                insights_payload = {
                    "company_name": enriched.get("company_name", ""),
                    "canonical_name": enriched.get("canonical_name", ""),
                    "summary": enriched.get("summary", ""),
                    "news": enriched.get("news", []),
                    "industry": enriched.get("industry", ""),
                    "website": enriched.get("website", ""),
                    "sources_used": enriched.get("sources_used", []),
                    "include_strategic_research": strategic_toggle.value
                }
                
                insights_data = call_api("/insights/", method="post", payload=insights_payload)
                analysis_progress.set_visibility(False)
                
                result_area.clear()
                nonlocal last_insights
                last_insights = {}

                if insights_data and insights_data.get('status') == 'success':
                    i = insights_data['insights'][0]
                    last_insights = i
                    with result_area:
                        ui.markdown(f"### 🏢 {i['company_name']}")
                        ui.markdown(f"**Industry:** {i.get('industry', 'Unknown')}")
                        if i.get('website'):
                            ui.markdown(f"**Website:** [{i['website']}]({i['website']})")
                        if i.get('summary'):
                            ui.markdown(f"**Overview:** {i['summary']}")

                        # --- Structured Strategic Insights ---
                        ui.markdown("### 📊 Strategic Assessment")
                        insights_text = i.get('strategic_insight', '')
                        if insights_text:
                            sections = re.split(r"\n?\d\)", insights_text)
                            for section in sections:
                                if section.strip():
                                    parts = section.split(" - ", 1)
                                    if len(parts) == 2:
                                        ui.markdown(f"**{parts[0].strip()}**")
                                        bullets = [s.strip() for s in parts[1].split(" - ") if s.strip()]
                                        for b in bullets:
                                            ui.markdown(f"• {b}")
                                    else:
                                        ui.markdown(f"• {section.strip()}")
                        else:
                            ui.markdown("No strategic analysis available.")

                        # --- News Section ---
                        if i.get('news'):
                            ui.markdown("### 📰 Recent Developments")
                            for news_item in i['news'][:3]:
                                ui.label(f"• {news_item}")

                        # --- Export PDF button ---
                        def export_pdf():
                            buffer = io.BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=letter)
                            styles = getSampleStyleSheet()
                            story = []

                            story.append(Paragraph(f"<b>Company Report: {i.get('company_name','')}</b>", styles['Title']))
                            story.append(Spacer(1, 12))
                            story.append(Paragraph(f"<b>Industry:</b> {i.get('industry','')}", styles['Normal']))
                            story.append(Paragraph(f"<b>Website:</b> {i.get('website','')}", styles['Normal']))
                            story.append(Spacer(1, 12))

                            story.append(Paragraph("<b>Overview</b>", styles['Heading2']))
                            story.append(Paragraph(i.get("summary","No overview available"), styles['Normal']))
                            story.append(Spacer(1, 12))

                            story.append(Paragraph("<b>Strategic Insights</b>", styles['Heading2']))
                            insights_text = i.get("strategic_insight", "")
                            if insights_text:
                                sections = re.split(r"\n?\d\)", insights_text)
                                for section in sections:
                                    if section.strip():
                                        parts = section.split(" - ", 1)
                                        if len(parts) == 2:
                                            story.append(Paragraph(f"<b>{parts[0].strip()}</b>", styles['Heading3']))
                                            bullets = [s.strip() for s in parts[1].split(" - ") if s.strip()]
                                            story.append(ListFlowable(
                                                [ListItem(Paragraph(b, styles['Normal'])) for b in bullets],
                                                bulletType='bullet'
                                            ))
                                        else:
                                            story.append(Paragraph(section.strip(), styles['Normal']))
                            else:
                                story.append(Paragraph("No strategic analysis available.", styles['Normal']))
                            story.append(Spacer(1, 12))

                            if i.get("news"):
                                story.append(Paragraph("<b>Recent News</b>", styles['Heading2']))
                                for news_item in i["news"][:3]:
                                    story.append(Paragraph(f"• {news_item}", styles['Normal']))

                            doc.build(story)
                            pdf_bytes = buffer.getvalue()
                            buffer.close()
                            ui.download(pdf_bytes, filename=f"{i['company_name']}_analysis.pdf")

                        ui.button("⬇️ Export as PDF", on_click=export_pdf).classes('bg-green-600 text-white px-4 py-2 rounded-lg mt-4')

                else:
                    ui.notify("❌ Strategic analysis generation failed.", color="red")

            ui.button(
                '🚀 Generate Business Assessment', 
                on_click=generate_action
            ).classes('bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 w-full')


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Business Intelligence Pro",
        host="0.0.0.0",  # required so Render can access it
        port=int(os.environ.get("PORT", 3000)),  # use Render's assigned port
        reload=False
    )

