# news-augment-cli

경제 기사 크롤링, 텍스트 증강, 카테고리 분류를 자동화한 Click 기반 CLI (경희대학교 학부연구장학, 2025.02)

## 개요

- 배경: 대학교 기자단이 경제 기사를 수동 분류하던 작업의 자동화
- 흐름: 대한경제 기사 크롤링(`crawling.py`) -> 특징어 추출 -> 본문 증강 -> 카테고리 분류와 근거 저장(`classify_article.py`)
- 모델: `gpt-4o-mini` (OpenAI API)
- 분류 결과에 근거(reason)를 함께 저장해 사후 검수 가능
- 성과(프로젝트 기준): 기자단 분류 업무 2시간 이상에서 10분 이내로 단축

## 파일 구성

| 파일 | 역할 |
|---|---|
| `crawling.py` | Selenium으로 대한경제 기사 제목과 본문 수집, `실시간 경제 기사 데이터.xlsx` 저장 |
| `classify_article.py` | 메인 CLI. 특징어 추출, 본문 증강, 분류, 인사이트 생성, `result_category.xlsx` 저장 |
| `categorized.py` | 초기 버전. 대분류별 키워드 사전으로 관련 기사 필터링(대화형) |
| `sample/` | 가상 샘플 입력(3행)과 실제 실행 결과 예시 |

## 설치

```
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."
```

- API 키는 코드에 넣지 않고 환경 변수 `OPENAI_API_KEY`에서만 읽음 (원본 코드도 동일 방식, 하드코딩 없음)
- 크롤링에는 Chrome과 chromedriver 필요

## 사용법

```
python classify_article.py --indir sample/sample_input.xlsx --sheet_name articles \
  --categories_sheet_name categories --categories categories --start 2025_01 --fin 2025_02
```

| 옵션 | 필수 | 설명 |
|---|---|---|
| `--indir` | 아니오 | 입력 Excel 경로 (실질적으로 필요) |
| `--sheet_name` | 아니오 | 기사가 있는 시트 이름 |
| `--categories` | 예 | 카테고리가 들어 있는 열 이름 |
| `--categories_sheet_name` | 예 | 카테고리 시트 이름 (같은 파일 안) |
| `--start`, `--fin` | 아니오 | 기간 필터(`YYYY_MM`), 둘 다 지정해야 함 |

`--help` 출력:

```
Usage: classify_article.py [OPTIONS]

Options:
  --indir TEXT                  The path to the Excel file.
  --sheet_name TEXT             The name of the sheet to access.
  --categories TEXT             The column name containing categories.
                                [required]
  --categories_sheet_name TEXT  The sheet_name which containing categories.
                                [required]
  --start TEXT                  Start period in YYYY_MM format.
  --fin TEXT                    End period in YYYY_MM format.
  --help                        Show this message and exit.
```

## 입력과 출력 형식

- 입력(기사 시트): `UUID`, `Title`, `Content`, `Date` 열 (기간 필터를 쓸 때 `Date` 필요)
- 입력(카테고리 시트): `--categories`로 지정한 열에 카테고리를 한 줄씩 기재. 시트만 수정하면 카테고리 변경 가능
- 출력: `result_category.xlsx` (시트 `output_data`)
- 출력 열: `UUID`, `category1`, `reason1`, `category2`, `reason2` (가능성 높은 2개 카테고리와 선정 이유)
- 터미널 출력: 추출 특징어, 증강 본문, 최빈과 최소 카테고리 기반 AI 인사이트
- 예시: `sample/sample_output.xlsx` (실제 실행 결과, 기사 원문 미포함)

## 카테고리 체계

- 대분류: 부동산, 증권, 보험, 복지, 사회 취약 계층, 기타 (`categorized.py`의 `CATEGORY_KEYWORDS`)
- 대분류별 소분류 키워드 예: 부동산(금리상승, 주택가격하락 등), 증권(주가상승, IPO 등)
- `classify_article.py`는 Excel 시트의 카테고리 목록을 사용하므로 체계를 코드 수정 없이 교체 가능

## 한계

- 글자수 부족 기사 선별 로직 없이 모든 기사를 증강함 (코드상 전 기사 증강)
- 증강 본문은 LLM 생성물로 사실 오류 가능, 출처 링크 요청은 프롬프트 수준
- 분류 응답이 JSON이 아니면 해당 기사는 빈 결과 처리
- 입력 읽기 실패 시 오류를 출력만 하고 계속 진행하며, 이후 단계에서 다시 오류가 날 수 있음
- 출력 파일명 고정(`result_category.xlsx`), 출력 경로 옵션 없음
- 기사 1건당 API 호출 3회 이상, 비용과 시간 발생
- `crawling.py`는 사이트 구조(CSS 선택자)에 의존하고 페이지 수가 코드에 고정(3쪽)
- 크롤링한 기사 원문과 빅카인즈 원본 데이터는 저작권과 이용약관 때문에 저장소에 포함하지 않음
- `categorized.py`는 초기 버전으로 입력 파일명이 고정되어 있음
