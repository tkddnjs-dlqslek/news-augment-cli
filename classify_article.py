import openai
import click
import json
import os
import yaml
import pandas as pd
from rich.console import Console

console = Console()

# 환경 변수에서 API 키를 가져옵니다.
api_key = os.getenv('OPENAI_API_KEY')  
openai.api_key = api_key

client = openai
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")


#gpt-4o-mini 모델을 사용하여 제목/본문에서 키워드 추출
def extract_keywords(content):
    # GPT-4o-mini 모델을 사용해 키워드 추출
    prompt = (
        f"다음 텍스트에서 주제에 맞는 가장 중요한 단어들을 개수에 상관없이 추출해줘:\n\n"
        f"\"{content}\"\n\n"
        "추출한 단어들은 쉼표로 구분해줘."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )
    
    #choices[0]은 실질적 대답의 내용
    keywords = completion.choices[0].message.content
    return keywords.split(",")

    
#추출한 키워드에 따라 기사 본문 내용을 증강
def augment_article(title, content, keywords):
    prompt = (
        f"기사 제목: {title}\n"
        f"기사 본문: {content}\n"
        f"특성: {keywords}\n\n"
        "기사 제목, 기사 본문, 특성을 모두 반영하여 기사 본문 내용을 1000자까지 늘려 작성해주세요."
        "실존하는 내용으로만 작성하고, 통계 자료를 사용한다면 출처 자료 링크를 꼭 남겨주세요."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content.strip()


#기사 제목, 증강된 기사 본문 내용을 기존 카테고리를 바탕으로 기사 분류 
def classify_article(title, augment_content, categories):
    """
    Classifies the article into predefined categories based on the title and content.
    """

    # 프롬프트 구성
    p1 = f"{title}\n\n{augment_content}\n" 
    
    #엑셀 파일에서 직접 가져올 수 있도록 만들어야 함
    # 동적으로 categories를 추가
    formatted_categories = "\\n".join(categories)
    p2 = f"위 기사는 다음 카테고리 중 어디에 해당되는가?:\n{formatted_categories}\n\n"
    
    #카테고리 이거 맞냐? value1에 이렇게..?
    p3 = f"""결과를 다음과 같은 형식으로 제시하라. "value1"에 예측 가능한 값을 배치하고 가장 확실한 2개의 값만을 제시하라. 선정 이유는 "value2", "value3"에 제시하라.\n{{"category1":"value1", "reason1":"value2","category2":"value2", "reason2":"value3"}}"""
    
    prompt = p1 + p2 + p3
         
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # 응답에서 결과 추출
    result_text = completion.choices[0].message.content.strip()

    # 응답 형식이 json이므로 json으로 형변환해서 출력
    try:
        result_json = json.loads(result_text)
        return result_json
    except json.JSONDecodeError:
        print("Error: The model's response could not be parsed as JSON.")
        print(result_text)
        return {}  # 빈 사전 반환

#cli 입력 부분
@click.command()
@click.option('--indir', help='The path to the Excel file.', required=False)
@click.option('--sheet_name', help='The name of the sheet to access.', required=False)
@click.option('--categories', help='The column name containing categories.', required=True)
@click.option('--categories_sheet_name', help='The sheet_name which containing categories.', required=True)
@click.option('--start', help='Start period in YYYY_MM format.', required=False)
@click.option('--fin', help='End period in YYYY_MM format.', required=False)
# @click.option('--outdir', help='The path to the Result file.', required=False)

# @click.option('--indir', help='The path to the Excel file.(indir precede input)', required=False)
# @click.option('--preference', help='Option file(.yaml).', required=False)
# @click.option('--help', help='Execute help file link to brouser.', required=False)

def main(indir, sheet_name, categories_sheet_name, categories, start, fin):
    
    try:
        # Excel 파일에서 특정 시트 읽기
        df = pd.read_excel(indir, sheet_name=sheet_name, engine='openpyxl')
        df_categories = pd.read_excel(indir, sheet_name=categories_sheet_name, engine="openpyxl")
        category_list = df_categories[categories].dropna().tolist()

        # 기간 필터링
        if start and fin:
            df = df[(df['Date'] >= start) & (df['Date'] <= fin)]
        elif start or fin:
            raise ValueError("Both --start and --fin must be provided together.")

    except Exception as e:
        console.print(f"An error occurred: {e}", style = "bold red")
    
    results = []
    
    for num in range(len(df["UUID"])):
        keywords = extract_keywords(df["Content"][num])
        console.print(f"Extracted Keywords: {keywords}", style = "bold underline magenta")

        augmented_article = augment_article(df["Title"][num], df["Content"][num], keywords)
        console.print(f"Augmented Article: \n{augmented_article}", style="bold blue", justify=True)

        # classify_article(df["Title"][num], augmented_article)

        classification = classify_article(df["Title"][num], augmented_article, category_list)
        
        
        results.append({
            "UUID": df["UUID"][num],
            **classification #dict 언패킹
        })

    # 최빈값, 최솟값 찾기
    category_counts = pd.DataFrame(results)[['category1', 'category2']].stack().value_counts()
    most_common = category_counts.idxmax()
    least_common = category_counts.idxmin()

    # AI 인사이트 생성
    insight_prompt = (
        f"최빈 카테고리는 {most_common}이며, 이는 해당 기간 동안 시의성이 높은 주제입니다."
        f" 가장 적게 나온 카테고리는 {least_common}이며, 이에 대한 이유를 분석해주세요."
    )

    insight_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 한국의 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": insight_prompt}
        ]
    )

    insight = insight_completion.choices[0].message.content.strip()
    console.print(f"AI Insight: \n{insight}", style="bold yellow")
        
    # 새로운 데이터프레임으로 변환
    output_df = pd.DataFrame(results)
    
    # 결과를 새로운 엑셀 파일로 저장
    output_df.to_excel('result_category.xlsx', index=False, sheet_name='output_data')

    console.print("Data saved to output_augmented_data.xlsx", style="bold green")
        
if __name__ == '__main__':
    main()
    
