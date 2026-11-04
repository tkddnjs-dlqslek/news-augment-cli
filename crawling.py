from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

driver = webdriver.Chrome()

# 타임아웃 시간 설정 (600초로 설정)
driver.set_page_load_timeout(600)

# 데이터셋 저장
dataset = {"Title": [], "Content": []}  # 데이터 누적을 위해 리스트로 저장

try:
    # 초기 페이지 접속
    driver.get("https://www.dnews.co.kr/uhtml/autosec/D_S1N2_S2N17_1.html")
    time.sleep(5)  # 페이지 로드 대기

    # 페이지 수 확인
    page_count = len(driver.find_elements(By.CSS_SELECTOR, "div.basePaging span.number a"))

    # 페이지별로 이동
    # 예시로 5 써놓음
    for page_index in range(3):
        try:
            # 페이지 번호 링크들 가져오기 (매번 새로 가져옴)
            page_links = driver.find_elements(By.CSS_SELECTOR, "div.basePaging span.number a")
            page_link = page_links[page_index]

            # 페이지 링크 클릭
            href = page_link.get_attribute("href")
            driver.get(href)
            time.sleep(3)  # 페이지 로드 대기

            # listBox_sub_main_s_l 클래스를 가진 div 내부의 모든 li 찾기
            list_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.listBox_sub_main_s_l ul li"))
            )

            # 각 li 내부의 a 태그 클릭
            for index, item in enumerate(list_items, start=1):
                try:
                    # li 안에 있는 a 태그 찾기
                    link = item.find_element(By.TAG_NAME, "a")
                    href = link.get_attribute("href")  # a 태그의 href 속성 가져오기
                    print(f"[Page {page_index + 1}] [{index}] 이동할 링크: {href}")

                    # 링크 클릭
                    link.click()
                    time.sleep(5)  # 새 페이지 로드 대기

                    # 데이터 추출
                    title = driver.find_element(By.CSS_SELECTOR, "div.newsCont > div.title").text
                    sub_title = driver.find_element(By.CSS_SELECTOR, "div.sub_title").text
                    texts = " ".join([p.text for p in driver.find_elements(By.CSS_SELECTOR, "div.text > p")])
                    all_text = sub_title + texts

                    # 데이터 추가
                    dataset["Title"].append(title)
                    dataset["Content"].append(all_text)
                    print(title)
                    print(all_text)

                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(10)  # 페이지 로드 대기
                except Exception as e:
                    print(f"[Page {page_index + 1}] [{index}] 에러 발생: {e}")

        except Exception as e:
            print(f"[Page {page_index + 1}] 에러 발생: {e}")

finally:
    # 드라이버 종료
    driver.quit()

# DataFrame으로 변환
df = pd.DataFrame(dataset)

# Excel 파일로 저장
output_file = "실시간 경제 기사 데이터.xlsx"
df.to_excel(output_file, sheet_name="input_sample", index=False)

print(f"엑셀 파일 '{output_file}'로 저장되었습니다.")
