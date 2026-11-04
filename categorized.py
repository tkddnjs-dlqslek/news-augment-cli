import yaml
from rich.console import Console
from rich.prompt import Prompt
import pandas as pd
import os
import openai
import sys

# UTF-8 인코딩 강제 설정
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# 카테고리와 키워드 설정
CATEGORY_KEYWORDS = {
    "부동산": [
        "금리상승", "금리하락", "금리유지", "대출실시/재개", "대출제한/중단", "대출금액증가", "대출금액감소",
        "주택가격상승", "주택가격하락", "연체율 상승", "연체율 하락", "주택거래증가", "주택거래감소",
        "경기침체", "경제활성화", "대출조건강화", "대출조건완화", "대출상환가속", "금리비교서비스", "정책"
    ],
    "증권": [
        "주가상승", "주가하락", "거래량증가", "거래량감소", "코스피지수상승", "코스피지수하락",
        "환율상승", "환율하락", "외환보유고증가", "외환보유고감소", "IPO", "주식분할",
        "주식매수", "주식매도", "배당금증가", "배당금감소", "투자유치", "펀드설정", "증권거래세"
    ],
    "보험": [
        "보험가입증가", "보험가입감소", "보험금청구증가", "보험금청구감소", "자동차보험", "생명보험",
        "건강보험", "손해보험", "보험료인상", "보험료인하", "보험약관변경", "보험상품출시",
        "소비자보호", "보험분쟁", "보장성보험", "저축성보험", "가입자혜택", "보험정책", "보험산업활성화"
    ],
    "복지": [
        "기초연금", "아동수당", "장애인수당", "노인복지", "저소득층지원", "실업급여",
        "의료비지원", "주거복지", "교육지원", "사회복지확대", "복지정책", "국민연금",
        "일자리창출", "생활안정지원", "취약계층보호", "긴급복지지원", "다문화가정지원", "사회서비스강화"
    ],
    "사회 취약 계층": [
        "장애인정책", "노숙인지원", "저소득가구지원", "다문화가족정책", "고령화대책", "청소년복지",
        "한부모가정지원", "사회적기업지원", "지역사회복지", "사회적약자보호", "취약계층고용정책",
        "사회적안전망강화", "생활안정지원", "차별철폐", "의료복지확대", "긴급구호"
    ],
    "기타": []  # 나머지 기사들이 분류될 카테고리
}

# CLI 상호작용 설정
console = Console()

def get_category_selection():
    while True:
        print("\n카테고리 목록:")
        for category in CATEGORY_KEYWORDS.keys():
            print(f"- {category}")

        choice = input("대분류 카테고리를 입력하세요 (키워드를 보려면 카테고리 이름 입력, 선택을 끝내려면 '종료' 입력): ")

        if choice == "종료":
            break

        if choice in CATEGORY_KEYWORDS:
            print(f"\n{choice} 소분류 키워드: {', '.join(CATEGORY_KEYWORDS[choice])}\n")
        else:
            print("잘못된 입력입니다. 다시 입력해주세요.")

    selected_categories = input("분류에 사용할 카테고리를 쉼표로 구분하여 입력하세요: ")
    return [cat.strip() for cat in selected_categories.split(",") if cat.strip() in CATEGORY_KEYWORDS]

# 환경 변수에서 API 키를 가져옵니다.
api_key = os.getenv('OPENAI_API_KEY')  
openai.api_key = api_key
client = openai

if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

# 엑셀 데이터 처리 및 필터링
input_file_path = "실시간 경제 기사 데이터.xlsx"  # crawling.py output (relative path)
output_file_path = "filtered_실시간_경제_기사_데이터.xlsx"


def filter_content_with_gpt(title, content, keywords, category):
    prompt = (
        f"다음 제목과 본문이 주어진 키워드와와 관련이 있는지 판단해주세요.\n\n"
        f"관련 키워드: {', '.join(keywords)}\n\n"
        f"제목: {title}\n"
        f"본문: {content}\n\n"
        f"관련이 있다면 {category}를 반환하고, 관련이 없다면 'non_related'를 반환해주세요. return하는 값이 다른 단어나 문장기호가 있으면 안 되고 오로지 {category}아니면 non_related 두 단어 중에 하나만 출력되어야 합니다."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 및 관련 분야의 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content.strip()

    return result


def main():
    selected_categories = get_category_selection()
    if not selected_categories:
        console.print("[red]카테고리가 선택되지 않아 작업을 종료합니다.[/red]")
        return

    # 엑셀 파일 읽기
    excel_data = pd.ExcelFile(input_file_path)
    data = excel_data.parse("input_sample")

    filtered_data = []

    # 각 선택된 카테고리에 대해 반복 처리
    for category in selected_categories:
        # 해당 카테고리의 키워드 가져오기
        keywords = CATEGORY_KEYWORDS[category]
        console.print(f"\n[bold]{category}에 대한 키워드:[/bold] {', '.join(keywords)}")

        for index, row in data.iterrows():
            title = row["Title"]
            content = row["Content"]
            
            # 카테고리별 필터링
            print(filter_content_with_gpt(title, content, keywords, category))
            if filter_content_with_gpt(title, content, keywords, category) == category:
                row["Category"] = category  # 현재 카테고리로 설정
                filtered_data.append(row)

    # DataFrame 생성
    filtered_df = pd.DataFrame(filtered_data, columns=list(data.columns) + ["Category"])

    if filtered_df.empty:
        console.print("[yellow]필터링된 데이터가 없습니다.[/yellow]")
        return

    # 카테고리별 정렬 및 단일 시트 저장
    grouped = filtered_df.sort_values(by="Category")  # Category 기준으로 정렬
    with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
        grouped.to_excel(writer, index=False, sheet_name="Sorted_Data")  # 정렬된 데이터를 단일 시트에 저장

    console.print(f"\n[green]필터링 작업이 완료되었습니다. 결과는 '{output_file_path}'에 저장되었습니다.[/green]")

if __name__ == "__main__":
    main()