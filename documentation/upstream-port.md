# x8y12pxDenkiChip v1.100 이식 조사

## 글리프 비교 (2026-11-02)

비교 대상은 이식 전 이 저장소의 `x10y12pxDenkiChipHangul.glyphs` v1.213과 원본 저장소의 `x8y12pxDenkiChip.glyphs` v1.100이다. 글리프 **이름**으로 비교했다. 이전 원본은 원본 저장소에서 해당 `.glyphs` 파일이 처음 추가된 커밋 `29eb3f4`의 v1.000이다.

| 구분 | 글리프 수 |
| --- | ---: |
| 한글판 전체 | 6,080 |
| 원본 v1.100 전체 | 3,787 |
| 두 파일에 공통으로 존재 | 1,460 |
| 한글판에만 존재 | 4,620 |
| 원본 v1.100에만 존재 | 2,327 |
| 원본 v1.000에 존재했으나 v1.100에 없는 이름 | 0 |

v1.000의 1,460개 이름은 모두 한글판과 v1.100에 존재한다. 따라서 **확인 가능한 이 기준에서는 원본의 삭제로 설명되는 한글판 전용 글리프가 없다.** 글리프 이름만 비교한 것이므로, 이름이 바뀐 글리프나 그보다 이전 이력은 별도로 확인해야 한다.

한글판에만 있는 4,620개는 유니코드 문자 이름과 글리프 이름을 이용해 다음과 같이 나뉜다.

- 4,522개: 유니코드 이름이 `HANGUL`로 시작하는 문자.
- 53개: `.kr` 접미사가 있는 한국어용 대체 글리프.
- 45개: 위 두 범주에 속하지 않는 글리프. 이 중 `standard-ko`, `won`, `won.full`은 한국 관련이며, 나머지에도 한국어에서 쓰일 수 있는 기호가 있다.

마지막 45개의 전체 목록은 다음과 같다. 아래 목록에 있다는 사실만으로 삭제 대상으로 판단해서는 안 된다.

- 합자: `f_f`, `f_f_i`, `f_f_l`, `fi`, `fl`.
- 한국 관련: `standard-ko`, `won`, `won.full`.
- 문자 및 기호: `crossMark`, `currency`, `dagger`, `daggerdbl`, `exclamdown`, `fahrenheit`, `figuredash`, `minute`, `notequal`, `paragraph`, `periodcentered`, `questiondown`, `second`, `threeemdash`, `triangularbullet`, `twoemdash`, `whiteBullet`.
- 음표 및 세로쓰기: `beamedsixteenthnotes-musical`, `beamedsixteenthnotes-musical.vert`, `quarternote-musical`, `quarternote-musical.vert`.
- 화살표 및 세로쓰기: `leftRightArrow`, `leftRightArrow.vert`, `northEastArrow`, `northEastArrow.vert`, `northWestArrow`, `northWestArrow.vert`, `southEastArrow`, `southEastArrow.vert`, `southWestArrow`, `southWestArrow.vert`, `upDownArrow`, `upDownArrow.vert`.
- 삼각형: `leftBlackTriangle`, `leftWhiteTriangle`, `rightBlackTriangle`, `rightWhiteTriangle`.

예를 들어 공통 글리프 `notedbl-musical.vert`는 한글판에서 폭이 800에서 1000으로 수정되어 있다. 단순히 이름이 공통인 글리프를 모두 덮어쓰면 이런 수정이 사라질 수 있다.

## Glyphs 4에서 이식 후보 만들기

이전 원본을 임시 파일로 추출한다. 이 파일은 원본에서 제거된 글리프와 기능 변경을 조사하는 기준으로 사용한다.

```sh
git -C /Users/quiple/Documents/GitHub/x8y12pxDenkiChip show \
  29eb3f4:sources/x8y12pxDenkiChip.glyphs > /private/tmp/x8y12pxDenkiChip-v1.000.glyphs
```

Glyphs 4의 Python 런타임과 프레임워크를 이용해 새 후보 파일을 생성한다. 필요하면 각 경로를 환경에 맞게 바꾼다.

```sh
'/Users/quiple/Library/Application Support/Glyphs 4/Repositories/Python/Python.framework/Versions/3.14/bin/python3' \
  scripts/port_upstream_glyphs4.py \
  --baseline /private/tmp/x8y12pxDenkiChip-v1.000.glyphs \
  --upstream /Users/quiple/Documents/GitHub/x8y12pxDenkiChip/sources/x8y12pxDenkiChip.glyphs \
  --target sources/x10y12pxDenkiChipHangul.glyphs \
  --output /private/tmp/x10y12pxDenkiChipHangul-ported.glyphs
```

스크립트는 원본에 존재하는 모든 글리프를 원본과 같게 만들고, 원본에 없는 한글판 글리프는 보존한다. 이전 원본에 있었으나 새 원본에서 빠진 항목도 보고만 하고 보존한다. 한글판의 기존 글리프 순서는 유지하며 새로운 원본 글리프는 뒤에 추가한다.

클래스, feature prefix, OpenType feature는 원본 코드를 유지하면서 한글판의 추가 규칙을 보존한다. 원본의 코드가 한글판에서 빠지거나 순서가 달라 안전하게 결합할 수 없다면 충돌을 보고하고 저장하지 않는다. 유니코드 중복, 마스터 ID·UPM 불일치, 커닝이 있어도 중단한다. 결과 파일을 Glyphs 4로 다시 열어 원본의 모든 글리프와 기능, 한글판 전용 글리프를 검증한다. 이미 존재하는 출력 파일은 덮어쓰지 않는다.

한글판의 글꼴 메타데이터, 마스터 설정, 인스턴스와 버전 번호는 유지한다. 원본의 해당 설정 변경이나 커닝은 자동 이식하지 않는다. `pixel` 등 공유 컴포넌트가 바뀌면 이를 참조하는 한글판 전용 글리프의 모양도 바뀔 수 있다. 결과를 채택하기 전에 Glyphs 4에서 화면과 실제 내보낸 글꼴을 확인한다.

2026-11-02 이식에서는 원본 글리프 2,327개를 추가하고 280개를 원본 내용으로 교체했다. 한글판 전용 글리프 4,620개를 보존했으며 `aalt`와 `ss01`을 원본에 맞춰 갱신하고 한글판의 `fwid`와 `vert` 추가 규칙은 유지했다. `notedbl-musical.vert`는 그림을 그대로 두고 폭을 1,000에서 원본과 같은 800유닛으로 되돌렸다.
