# x10y12pxDenkiChipHangul 「전기칩 한글」

[데모](https://blog.quiple.dev/font/denkichip-hangul)

<strong>x10y12pxDenkiChipHangul(전기칩 한글)</strong>은 [患者長ひっく](https://x.com/hicchicc) 님께서 제작한 12px 크기의 일본어 픽셀 폰트 '**[x8y12pxDenkiChip(でんきチップ)](https://github.com/hicchicc/x8y12pxDenkiChip)**'을 기반으로 만들어진 하는 한국어&middot;일본어 픽셀 폰트입니다.

Adobe-KR-9 보충 0의 한글 음절 2,780자와 일본 한자 640자를 지원합니다.

## 라이선스

| 범주 | 설명 |
| - | - |
| 상업적 이용 | **✅ 가능**<br />폰트를 상업적으로 이용할 수 있습니다. 표현하는 내용이나 매체 등도 상관하지 않습니다. |
| 임베드 | **✅ 가능**<br />폰트 파일을 게임&middot;소프트웨어 등에 포함시키거나 웹 폰트로 이용할 수 있습니다. |
| 출처 표기 | **✅ 필수 아님**<br />폰트의 출처 및 저작자명을 표시하지 않아도 됩니다. |
| 수정 및 재배포 | **✅ 가능**<br />폰트를 수정하거나 재배포할 수 있습니다. 수정하여 재배포할 경우 OFL-1.1을 채택해야 합니다. |
| 단독 판매 | **❌ 금지**<br />폰트 파일을 단독으로 유료 판매하는 경우. 게임&middot;소프트웨어 등에 포함시켜 판매하는 것은 가능합니다. |
| 이용으로 인한 피해 | **❌ 책임 안 짐**<br />폰트의 이용으로 인한 피해나 손해가 생기더라도 일절 책임지지 않습니다. |

&copy; 2026 Lee Minseo (<quiple@quiple.dev>)

&copy; 2026 The x8y12pxDenkiChip Project Authors (<https://github.com/hicchicc/x8y12pxDenkiChip>)

전기칩 한글은 SIL 오픈 폰트 라이선스 1.1에 따라 이용할 수 있습니다.

## 제작에 사용된 도구

- [Glyphs 3](https://glyphsapp.com)

## 폰트 빌드

macOS에서 다음 항목을 준비합니다.

- Glyphs 3.5 이상과 유효한 라이선스
- [`quiple/BDFFileFormat`](https://github.com/quiple/BDFFileFormat) 저장소의 `BDF` 플러그인 (Glyphs 3에 설치)
- Python 3.10 이상

저장소 루트에서 Glyphs 공식 CLI를 프로젝트 전용 환경에 한 번 설치합니다.

```sh
make setup
```

이후 폰트를 저장하고 다음 명령을 실행합니다.

```sh
make
```

`fonts/`에 OTF, TTF, TrueType 기반 WOFF2, BDF를 출력합니다. 이 빌드는 [Glyphs 공식 CLI](https://pypi.org/project/glyphs-cli/)를 사용합니다. OTF, TTF, WOFF2는 겹침 제거를 적용하고 자동 힌팅은 적용하지 않습니다.

Glyphs 앱의 위치가 기본값과 다르면 다음과 같이 지정할 수 있습니다.

```sh
make GLYPHS_APP="/path/to/Glyphs 3.app"
```

생성한 파일만 지우려면 `make clean`을 실행합니다.
