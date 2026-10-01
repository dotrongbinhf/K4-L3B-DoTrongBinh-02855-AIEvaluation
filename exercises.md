# Day 14 — Exercises

## AI Evaluation & Benchmarking · Lab Worksheet

**Thời gian làm bài:** 9:15–12:00

**Domain:** OrbitTech Store Customer Support

Điền trực tiếp câu trả lời vào file này. Golden dataset 20 QA được viết một lần
duy nhất trong `golden_dataset.json`, không chép lại toàn bộ vào Markdown.

---

Từ 9:15–9:30, cài môi trường và chạy baseline tests theo `guide_lab.md`.

---

## Part 1 — Warm-up (9:30–9:45)

### Exercise 1.1 — RAGAS Metric Thresholds

Theo bài giảng:

- 0.8–1.0: Good — monitor, maintain.
- 0.6–0.8: Needs work — analyze failures, iterate.
- Dưới 0.6: Significant issues — investigate.

Với từng metric, xác định khi nào score thấp có thể chấp nhận và khi nào là
critical.

| Metric | Acceptable Low Score Scenario | Critical Low Score Scenario | Action Required |
|---|---|---|---|
| Faithfulness | Thấp nhẹ ở câu trả lời rủi ro thấp có chủ ý từ chối khẳng định khi corpus thiếu bằng chứng, kiểm tra mẫu để xác nhận không có claim sai. | Thấp vì câu trả lời bịa hoặc khẳng định chính sách, giá, bảo hành hay bảo mật không được evidence hỗ trợ. | Kiểm tra claim và evidence theo từng mẫu, sửa retrieval hoặc prompt. Chặn phát hành nếu có hallucination về thông tin quan trọng. |
| Answer Relevance | Điểm thấp do câu hỏi nhiều ý hoặc cách diễn đạt khác từ vựng trong khi câu trả lời vẫn xử lý đúng yêu cầu. | Trợ lý trả lời nhầm sản phẩm/vấn đề, lạc đề hoặc bỏ qua ý định chính của khách hàng. | Kiểm tra intent và các nhóm câu hỏi, cải thiện phân loại ý định/prompt, thêm case bị bỏ sót vào golden set. |
| Context Recall | Có thể chấp nhận thấp khi câu hỏi chỉ cần một fact hẹp và fact đó đã có trong context được dùng, xác minh thủ công rằng không bỏ sót evidence cần thiết. | Retriever bỏ mất một điều kiện, ngoại lệ hoặc nhiều evidence cần cho câu hỏi nhiều bước, khiến câu trả lời thiếu hoặc sai. | Bổ sung/chỉnh chunking, query expansion hoặc retrieval, phân tích recall theo nhóm câu hỏi. |
| Context Precision | Có thể chấp nhận thấp nhẹ khi top-k vẫn chứa đủ evidence đúng nhưng kèm vài chunk dư thừa, với chi phí và tác động nhỏ. | Top-k bị chiếm bởi chunk không liên quan, đẩy evidence quan trọng xuống thấp hoặc làm phát sinh câu trả lời sai. | Kiểm tra thứ hạng top-k, cải thiện filter/reranker và giới hạn nội dung nhiễu. |
| Completeness | Có thể chấp nhận khi câu hỏi đơn giản và câu trả lời ngắn vẫn đáp ứng đủ mọi ý được hỏi, dù reference có thêm chi tiết tùy chọn. | Bỏ thiếu bước, điều kiện, giới hạn, ngoại lệ hoặc một phần được hỏi có ảnh hưởng đến quyết định của khách. | So với các ý chính trong reference, thêm evidence/case còn thiếu và cải thiện hướng dẫn sinh câu trả lời. |

### Exercise 1.2 — Bias trong LLM-as-a-Judge

Ba bias thường gặp:

- Position bias: judge ưu tiên answer xuất hiện trước.
- Verbosity bias: judge ưu tiên answer dài hơn.
- Self-preference: judge ưu tiên output giống chính model đó.

**Câu 1: Thiết kế experiment phát hiện position bias với ít nhất hai conditions.**

> Tạo tập câu hỏi có đáp án ứng viên A và B, giữ nguyên nội dung, rubric và độ dài tương đương. Ở condition 1, đưa A trước B, ở condition 2, đảo thành B trước A. Cho judge chấm độc lập cùng một cặp ở cả hai thứ tự trên nhiều câu hỏi, ngẫu nhiên hóa thứ tự chạy, rồi so sánh điểm và tỷ lệ người thắng. Nếu điểm hoặc winner thường đổi theo vị trí thay vì theo chất lượng nội dung thì có position bias.

**Câu 2: Làm thế nào giảm verbosity bias bằng rubric design?**

> Chấm theo các tiêu chí nguyên tử có trọng số, mỗi tiêu chí mô tả bằng chứng cần có để đạt từng mức điểm. Nêu rõ câu trả lời ngắn nhưng đủ ý nhận điểm tối đa, độ dài, văn phong và chi tiết lặp lại không tự cộng điểm. Chỉ tính độ rõ ràng khi nó ảnh hưởng đến việc đáp ứng tiêu chí.

**Câu 3: Tại sao cần calibrate LLM judge với human labels?**

> So sánh judge với nhãn của người đánh giá giúp đo độ đồng thuận, phát hiện thiên lệch hoặc sai lệch có hệ thống, và hiệu chỉnh rubric cùng ngưỡng theo mức độ rủi ro thực tế. Dùng một tập human-labeled đại diện, giữ lại một phần để kiểm tra sau hiệu chỉnh nhằm tránh chỉ khớp với các ví dụ đã xem.

### Exercise 1.3 — Evaluation trong CI/CD

**Câu 1: Chọn threshold để block deployment.**

| Metric | Threshold | Lý do |
|---|---:|---|
| Faithfulness | 0.85 | Trung bình benchmark tối thiểu cao vì claim không có căn cứ có thể gây hại, mọi hallucination nghiêm trọng cần chặn phát hành dù điểm trung bình đạt. |
| Answer Relevance | 0.75 | Đảm bảo phần lớn câu trả lời xử lý đúng intent, xem riêng các nhóm intent có điểm thấp trước khi phát hành. |
| Completeness | 0.75 | Giảm nguy cơ thiếu bước hoặc điều kiện quan trọng, ưu tiên kiểm tra các case chính sách và nhiều ý. |

**Câu 2: Khi nào dùng offline evaluation, online evaluation và human review?**

> Dùng offline evaluation trên golden set trước merge/release để so sánh phiên bản, tìm regression và chạy lặp lại được. Dùng online evaluation sau triển khai để theo dõi traffic thật, drift và chỉ số sản phẩm, rollout dần và có thể rollback khi cần. Dùng human review cho mẫu ngẫu nhiên định kỳ, case rủi ro cao, khi judge và metric bất đồng, hoặc khi điều tra lỗi để xác nhận nhãn và quyết định cách sửa.

---

## Part 2 — Core Coding (9:45–10:40)

Hoàn thiện các TODO bắt buộc trong `template.py`.

### Task 1 — Data Models

- `QAPair`: question, expected answer, gold context, metadata và retrieved contexts.
- `EvalResult`: answer-side scores, optional retrieval scores, pass/failure fields.
- `overall_score()`: trung bình Faithfulness, Relevance và Completeness.

### Task 2 — RAGASEvaluator

Answer-side:

- `evaluate_faithfulness(answer, context)`
- `evaluate_relevance(answer, question)`
- `evaluate_completeness(answer, expected)`

Retrieval-side:

- `evaluate_context_recall(contexts, expected)`
- `evaluate_context_precision(contexts, expected)`

Full pipeline:

- `run_full_eval(..., contexts=None)` luôn tính ba answer metrics.
- Nếu có `contexts`, tính và lưu thêm Context Recall và Context Precision.
- Retrieval scores không làm thay đổi `overall_score()` và pass rule gốc.

### Task 3 — LLMJudge

- `score_response(question, answer, rubric)`
- `detect_bias(scores_batch)`

### Task 4 — BenchmarkRunner

- `run(qa_pairs, agent_fn, evaluator)`
- `generate_report(results)`
- `run_regression(new_results, baseline_results)`
- `identify_failures(results, threshold)`

`BenchmarkRunner.run()` phải truyền `pair.retrieved_contexts` vào
`run_full_eval()`. Report phải có average của hai retrieval metrics.

### Task 5 — FailureAnalyzer

- `categorize_failures(failures)`
- `find_root_cause(failure)`
- `generate_improvement_suggestions(failures)`
- `generate_improvement_log(failures, suggestions)`

Kiểm tra:

```bash
pytest tests/ -v
```

`rerank_by_overlap()` là TODO bonus của Exercise 3.5. Test tương ứng được skip
nếu bạn chưa làm bonus.

---

## Part 3 — Golden Dataset & Real Benchmark (10:40–11:35)

### Exercise 3.1 — Build the Golden Dataset

Thiết kế và validate dataset theo Mục 5–6 trong `guide_lab.md`. Nội dung 20 QA
được điền trực tiếp trong `golden_dataset.json`; phần dưới chỉ ghi lại kết quả
và quyết định thiết kế, không chép lại toàn bộ QA.

**Kết quả dataset**

| Hạng mục | Kết quả |
|---|---|
| Tổng số records | ____ / 20 |
| Easy | ____ / 5 |
| Medium | ____ / 7 |
| Hard | ____ / 5 |
| Adversarial | ____ / 3 |
| Source documents được sử dụng | ____ / 10 |
| Validator status | PASS / FAIL |

**Ba case đại diện cho quyết định thiết kế**

| ID | Difficulty | Source document(s) | Vì sao case phù hợp với difficulty/attack type? |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

**Điểm khó nhất khi xây dựng expected answer hoặc evidence là gì?**

> *Câu trả lời:*

**Xác nhận:**

- [ ] Mọi claim trong expected answer đều có evidence hỗ trợ.
- [ ] Không có questions trùng ý và không dùng kiến thức ngoài corpus.
- [ ] `python validate_golden_dataset.py` báo `PASS`.

### Exercise 3.2 — Benchmark Run

Chạy:

```bash
python domain_assistant.py
python evaluate_answers.py
```

Copy bảng terminal vào đây hoặc điền từ `artifacts/benchmark_results.json`.

| ID | Question (short) | Ctx Recall | Ctx Precision | Faithfulness | Relevance | Completeness | Overall | Passed? | Failure Type |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| E01 | | | | | | | | | |
| E02 | | | | | | | | | |
| E03 | | | | | | | | | |
| E04 | | | | | | | | | |
| E05 | | | | | | | | | |
| M01 | | | | | | | | | |
| M02 | | | | | | | | | |
| M03 | | | | | | | | | |
| M04 | | | | | | | | | |
| M05 | | | | | | | | | |
| M06 | | | | | | | | | |
| M07 | | | | | | | | | |
| H01 | | | | | | | | | |
| H02 | | | | | | | | | |
| H03 | | | | | | | | | |
| H04 | | | | | | | | | |
| H05 | | | | | | | | | |
| A01 | | | | | | | | | |
| A02 | | | | | | | | | |
| A03 | | | | | | | | | |

**Aggregate Report**

- Overall pass rate: ____%
- Avg Context Recall: ____
- Avg Context Precision: ____
- Avg Faithfulness: ____
- Avg Relevance: ____
- Avg Completeness: ____
- Failure type distribution: ____

**Ba cases có Overall Score thấp nhất**

1. ID: ____ | Score: ____ | Failure type: ____
2. ID: ____ | Score: ____ | Failure type: ____
3. ID: ____ | Score: ____ | Failure type: ____

**Nhận xét ngắn:** Metric nào yếu nhất? Kết quả gợi ý vấn đề nằm ở retrieval
hay generation?

> *Câu trả lời:*

### Exercise 3.3 — LLM-as-a-Judge Rubric Design

Thiết kế rubric domain-specific cho OrbitTech Customer Support. Mỗi mức phải
đủ cụ thể để hai người chấm độc lập có thể hiểu giống nhau.

Chọn 3–5 dimensions:

- [x] Correctness
- [x] Completeness
- [ ] Relevance
- [x] Evidence/citation
- [x] Actionability
- [x] Safety/privacy
- [ ] Tone/clarity
- [ ] Dimension khác: __________

| Score | Tiêu chí domain-specific | Ví dụ response |
|---:|---|---|
| 5 | Chính xác theo policy/KB đang có hiệu lực; giải quyết mọi ý hỏi; dẫn đúng nguồn cho claim về sản phẩm/tài khoản; nêu bước tiếp theo cụ thể; không yêu cầu dữ liệu bí mật. | “Theo bài hướng dẫn [ID], hãy thử các bước A và B. Nếu vẫn chưa được, liên hệ hỗ trợ qua kênh chính thức; không gửi mật khẩu hoặc mã xác minh.” |
| 4 | Không có lỗi quan trọng; có nguồn và hướng xử lý an toàn, nhưng thiếu một chi tiết phụ như bước tiếp theo nếu cách đầu thất bại. | Nêu đúng bước A và nguồn [ID], nhưng không nói người dùng nên làm gì nếu A không hiệu quả. |
| 3 | Có hướng trả lời đúng một phần nhưng bỏ sót một yêu cầu chính, hoặc có claim chưa được nguồn hỗ trợ; người dùng cần hỏi lại để xử lý xong. | Nêu bước A đúng nhưng không trả lời phần B của câu hỏi và không dẫn nguồn cho claim còn lại. |
| 2 | Sai hoặc thiếu phần lớn hướng dẫn cần thiết; nguồn không khớp hoặc không có; hành động đề xuất khó thực hiện nhưng chưa gây rủi ro nghiêm trọng. | Chỉ bảo “thử lại sau” dù policy/KB có hướng dẫn phù hợp, không nêu bước hay nguồn kiểm tra. |
| 1 | Trái policy/KB, bịa quyền lợi hoặc kết quả; yêu cầu mật khẩu/mã OTP/dữ liệu nhạy cảm; hoặc hoàn toàn không trả lời câu hỏi. | Khẳng định một khoản hoàn tiền không có trong policy, yêu cầu gửi OTP qua chat, hoặc trả lời lạc đề. |

**Ba edge cases khó chấm**

| Edge Case | Tại sao khó chấm? | Rubric xử lý thế nào? |
|---|---|---|
| Hai bài KB đưa ra hướng xử lý hoặc điều kiện khác nhau | Không thể chấm chỉ theo mức độ tự tin của câu trả lời; tài liệu có thể khác phiên bản hoặc phạm vi áp dụng. | Chỉ dùng nguồn được phê duyệt và còn hiệu lực; nếu chưa xác định được nguồn áp dụng, nêu giới hạn và chuyển hỗ trợ thay vì tự chọn policy. |
| Người dùng gửi mật khẩu/OTP hoặc yêu cầu judge xử lý thông tin tài khoản riêng | Câu trả lời có thể hữu ích nhưng vô tình lặp lại hay khuyến khích chia sẻ bí mật. | Điểm Safety/Privacy tối đa chỉ khi không lặp lại bí mật, nhắc không chia sẻ và hướng sang kênh xác thực chính thức; yêu cầu bí mật làm điểm này bằng 1. |
| Một bước khắc phục đã giúp nhưng người dùng còn câu hỏi phụ hoặc vấn đề chưa giải quyết | “Có ích” không đồng nghĩa đã trả lời đầy đủ; mức độ hoàn tất phụ thuộc từng ý hỏi. | Chấm riêng từng ý trong Completeness; ghi nhận bước đúng nhưng trừ điểm phần còn thiếu, đồng thời yêu cầu nêu bước tiếp theo hoặc điều kiện escalation. |

**Bias controls:** Rubric hoặc evaluation protocol của bạn giảm position bias,
verbosity bias và self-preference bằng cách nào?

> Ẩn tên model và nguồn tạo câu trả lời trước khi chấm; xáo trộn thứ tự các response, rồi chấm lại một phần cặp A/B sau khi đảo vị trí để so sánh điểm theo vị trí. Rubric cho điểm theo claim, ý cần giải quyết, nguồn và bước an toàn; câu ngắn nhưng đủ bằng chứng có thể đạt điểm tối đa, còn độ dài/lặp ý không được cộng điểm. Để kiểm soát self-preference, dùng judge khác model/provider với model sinh answer, không tiết lộ danh tính model, và đối chiếu định kỳ với nhãn của người chấm độc lập trên tập đại diện; phân xử bất đồng rồi cập nhật rubric.

### Exercise 3.4 — Framework Comparison (Bonus +5)

Chỉ làm sau khi hoàn thành 3.1–3.3. Chọn hai framework trong RAGAS, DeepEval
và TruLens; chạy hoặc thiết kế một so sánh có cùng input dataset.

| Tiêu chí | Framework 1: ____ | Framework 2: ____ |
|---|---|---|
| Setup complexity | | |
| Metrics available | | |
| CI/CD integration | | |
| Kết quả trên cùng dataset | | |
| Insight rút ra | | |

- Scores có nhất quán không?
- Framework nào strict hơn và vì sao?
- Hai framework có tìm ra cùng failure cases không?

> *Phân tích:*

### Exercise 3.5 — Retrieval Reranking (Bonus +5)

Mục tiêu: kiểm tra việc đổi thứ tự chunks có tăng Context Precision mà không
thay đổi Context Recall hay không.

1. Chọn ít nhất 5 cases từ `artifacts/actual_answers.json`.
2. Tính Context Recall và Context Precision trước rerank.
3. Implement `rerank_by_overlap()` hoặc một reranker khác.
4. Rerank cùng tập chunks, không thêm hoặc xóa chunk.
5. Tính lại hai metrics và giải thích kết quả.

| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |
|---|---:|---:|---:|---:|---:|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| **Avg** | | | | | |

**Tại sao Recall dự kiến không đổi?**

> *Câu trả lời:*

**Khi nào reranking không đủ và cần sửa retriever/query/chunking?**

> *Câu trả lời:*

---

## Part 4 — Reflection (11:35–11:50)

Hoàn thành `reflection.md` bằng kết quả thật từ Exercise 3.2.

---

## Completion Checklist

Hoàn thành kiểm tra cuối trong khoảng 11:50–12:00.

- [ ] Tất cả required tests pass.
- [ ] `golden_dataset.json` validate thành công.
- [ ] Exercise 3.1 hoàn thành trong file JSON và bảng kết quả phía trên.
- [ ] Exercise 3.2 có năm metrics, aggregate report và ba cases thấp nhất.
- [ ] Exercise 3.3 có rubric 1–5 và bias controls.
- [ ] `reflection.md` có ba failure analyses và regression strategy.
- [ ] Đã copy `template.py` thành `solution/solution.py`.
- [ ] Exercise 3.4 và 3.5 chỉ làm nếu chọn bonus.
