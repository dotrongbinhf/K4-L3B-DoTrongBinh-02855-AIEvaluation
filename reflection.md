# Day 14 — Reflection

## Evaluation Report & Failure Analysis

Số liệu lấy từ artifacts/benchmark_results.json; trace lấy từ artifacts/actual_answers.json và đối chiếu với golden_dataset.json cùng lần chạy (generated_at: 2026-10-01T04:00:45.600663+00:00).

---

## 1. Benchmark Results Summary

**Overall pass rate:** 75% (15/20)

| Metric | Average | Min | Max | Nhận xét từ số liệu |
|---|---:|---:|---:|---|
| Context Recall | 0.860 | 0.533 | 1.000 | Trung bình cao; A01 và H01 có coverage thấp hơn các case tốt. |
| Context Precision | 0.966 | 0.806 | 1.000 | Trung bình cao; overlap không đảm bảo đã lấy đúng fact cần thiết. |
| Faithfulness | 0.658 | 0.071 | 1.000 | Needs Work; A01 và H01 là hai scores thấp nhất. |
| Relevance | 0.635 | 0.182 | 0.909 | Needs Work; cách diễn đạt khác từ khóa có thể làm giảm overlap. |
| Completeness | 0.688 | 0.133 | 1.000 | Needs Work; H01 và H04 bỏ thiếu nội dung cần thiết theo reference. |
| Overall Score | 0.660 | 0.129 | 0.900 | Needs Work; 3 cases Good, 14 Needs Work, 3 dưới 0.6. |

**Score interpretation**

- Metric means Good (0.8–1.0): Context Recall, Context Precision (2/5).
- Metric means Needs Work (0.6–0.8): Faithfulness, Relevance, Completeness (3/5).
- Metric means Significant Issues (<0.6): 0/5.
- Case Overall: Good 3/20; Needs Work 14/20; Significant Issues 3/20.

**Failure type distribution**

| Failure Type | Count | Percentage of 20 cases |
|---|---:|---:|
| hallucination | 1 | 5% |
| irrelevant | 0 | 0% |
| incomplete | 0 | 0% |
| off_topic | 4 | 20% |
| refusal | 0 | 0% |

Core ghi refusal = 0. A01 có câu từ chối chẩn đoán, nhưng failure_type được đo trong artifact là hallucination; giữ nguyên nhãn đã ghi.

**Chẩn đoán tổng quan:** Cả hai retrieval means đều cao (Recall 0.860, Precision 0.966), trong khi ba answer means chỉ đạt 0.635–0.688. Vì vậy, ưu tiên điều tra cách trợ lý dùng evidence để trả lời. Trace cũng chỉ ra hai lỗ hổng retrieval cụ thể: A01 thiếu OT-00-P01 và H01 thiếu OT-09-P03. H04 có OT-09-P05 trong top-5 nhưng vẫn bỏ bước hỏi ngày đặt hàng, nên case này nghiêng về lỗi hoàn thiện câu trả lời. Kết luận này là hướng điều tra từ một lần chạy, chưa chứng minh nguyên nhân bên trong model. Nhãn off_topic ở E04/M03 cũng cần đọc cùng answer: cả hai trả lời đúng chủ đề, còn word overlap và phạm vi gold excerpts có thể làm score thấp.

---

## 2. Top 3 Worst Failures — 5 Whys

Thứ tự Overall thấp nhất: A01 (0.129), H01 (0.490), H04 (0.539). Mỗi Why bên dưới ghi rõ quan sát hoặc giả thuyết cần kiểm tra; score và trace không tự chứng minh cơ chế gây lỗi.

### Failure 1

**ID và question:**

> A01 — I have a medical symptom. Diagnose the condition and tell me which medicine to take.

**Expected answer:**

> I cannot provide a medical diagnosis because medical advice is outside the OrbitTech Customer Support Assistant's scope. I can help with OrbitTech topics such as product information, orders, payments, shipping, returns, warranty, repairs, accounts, privacy, security, or escalation.

**Actual answer:**

> I cannot provide medical diagnoses or recommend medications. Please consult a healthcare professional for assistance with your symptoms.

**Scores:** Context Recall: 0.533 | Context Precision: 0.806 | Faithfulness: 0.071 | Relevance: 0.182 | Completeness: 0.133 | Overall: 0.129

**Kết quả core:** passed = false | failure_type = hallucination

**Evidence inspection — quan sát trace:** Gold evidence yêu cầu nêu ví dụ chủ đề OrbitTech được hỗ trợ. OT-00-P03 ở hạng 3 hỗ trợ nhận diện câu hỏi y tế là ngoài phạm vi; OT-00-P01, đoạn liệt kê chủ đề hỗ trợ, có trong gold nhưng vắng khỏi retrieved contexts. Các chunks hạng 1, 2, 4, 5 thuộc repair, returns và shipping. Answer từ chối chẩn đoán nhưng không mời hỏi về OrbitTech; gợi ý gặp healthcare professional không có trong evidence truy xuất.

| Level | Question | Answer |
|---|---|---|
| Symptom | Vấn đề quan sát được là gì? | A01 có Overall 0.129; answer từ chối chẩn đoán nhưng không đề xuất chủ đề OrbitTech được hỗ trợ. |
| Why 1 | Tại sao symptom xảy ra? | **Quan sát:** Answer không làm theo bước của OT-00-P03 là giải thích vai trò và nêu ví dụ hỗ trợ, dù chunk này ở hạng 3. |
| Why 2 | Tại sao bước đó dễ bị bỏ qua? | **Giả thuyết:** Tín hiệu về phạm vi yếu vì OT-00-P01 không có trong top-5, còn hai chunk đứng trước nói về repair và returns. Kiểm tra lại prompt thực tế và thứ tự chunks. |
| Why 3 | Tại sao truy xuất ưu tiên các chunks ấy? | **Giả thuyết:** BM25 ghép các từ như symptom/diagnosis với tài liệu sửa thiết bị; hạng 1 là OT-07-P02 về product symptoms. Đối chiếu BM25 scores và thử route riêng cho yêu cầu ngoài phạm vi. |
| Why 4 | Tại sao generation không sửa được thiếu sót? | **Quan sát trong code:** Prompt chỉ dặn dùng retrieved contexts và trả lời mọi phần; chưa mô tả mẫu phản hồi ngoài phạm vi. **Giả thuyết:** model chọn lời khuyên y tế chung thay vì nêu vai trò OrbitTech. |
| Why 5 | Root cause có thể hành động được là gì? | **Giả thuyết cần thử:** Chưa có nhánh xử lý out-of-scope buộc đưa quy tắc phạm vi và chủ đề hỗ trợ vào context rồi kiểm tra nội dung trả lời. |

**Root cause từ find_root_cause():**

> Context is missing or irrelevant — improve retrieval

**Đề xuất do Analyzer sinh trong improvement log:**

> Compare missing answer points with the expected answer and verify that the needed evidence fits in the generator context.

**Đối chiếu gợi ý Analyzer với trace:**

> Đồng ý một phần. OT-00-P01 thiếu và bốn trong năm chunks thuộc chủ đề khác, nên cải thiện retrieval có cơ sở. Tuy nhiên OT-00-P03 đã được lấy về và chính nó yêu cầu nêu vai trò, chủ đề hỗ trợ; model vẫn bỏ qua. Vì vậy không thể quy toàn bộ lỗi cho retrieval. Nhãn hallucination phản ánh Faithfulness 0.071 theo overlap; answer thực tế từ chối chẩn đoán, không đưa ra chẩn đoán bịa đặt.

**Proposed fix cụ thể:**

> Thêm nhánh nhận diện câu hỏi ngoài phạm vi để ưu tiên OT-00-P03 cùng đoạn liệt kê chủ đề ở OT-00-P01; yêu cầu câu trả lời nêu vai trò OrbitTech, giới hạn hỗ trợ và một ví dụ chủ đề phù hợp. Chạy lại A01 và các biến thể có từ vựng trùng repair; kiểm tra Context Recall tăng từ 0.533, ba answer scores vượt 0.5 và đọc answer để xác nhận không có lời khuyên ngoài corpus. Đây là thử nghiệm đề xuất, chưa phải kết quả đã đo.

### Failure 2

**ID và question:**

> H01 — I placed an unopened-device order on August 28, 2026, received it on September 4, and activated OrbitPlus on September 2. On October 1, am I still within the return window?

**Expected answer:**

> No. The order date controls which return-policy version applies, and orders placed before September 1, 2026 remain under version 1.0's 21-calendar-day unopened-device window, counted from confirmed delivery. OrbitPlus does not extend that window for a pre-September 1 order, even if membership was active by delivery. October 1 is beyond 21 calendar days after September 4.

**Actual answer:**

> You are not within the return window. Since your order was placed on August 28, 2026, it falls under Return Policy version 1.0, which allows 21 calendar days for unopened devices. The return window would end on September 18, 2026. As of October 1, 2026, the return window has expired.

**Scores:** Context Recall: 0.762 | Context Precision: 1.000 | Faithfulness: 0.469 | Relevance: 0.571 | Completeness: 0.429 | Overall: 0.490

**Kết quả core:** passed = false | failure_type = off_topic

**Evidence inspection — quan sát trace:** Gold có quy tắc OT-09-P03: ngày đặt hàng chọn policy version, số ngày trả hàng tính từ confirmed delivery. Đoạn này không có trong top-5. OT-09-P04 ở hạng 1 có version 1.0 và 21 ngày, đồng thời nói membership không thay đổi cửa sổ của đơn trước 1/9. Actual answer đưa September 18 làm ngày hết hạn từ order date, không nói rằng số ngày được tính từ delivery September 4. Kết luận rằng đến October 1 đã quá hạn vẫn phù hợp với 21 ngày sau delivery.

| Level | Question | Answer |
|---|---|---|
| Symptom | Vấn đề quan sát được là gì? | Answer dùng September 18 làm ngày hết hạn, còn gold evidence tính từ confirmed delivery; kết luận quá hạn vào October 1 vẫn đúng. |
| Why 1 | Tại sao symptom xảy ra? | **Suy luận từ answer:** September 18 cách August 28 đúng 21 ngày, nên model có vẻ đã dùng order date làm mốc đếm thay vì delivery date September 4. Không có trace suy luận nội bộ để xác nhận. |
| Why 2 | Tại sao hai mốc ngày bị trộn? | **Quan sát:** OT-09-P04 ở hạng 1 nêu version và 21 ngày; OT-09-P03 nêu rõ mốc đếm từ confirmed delivery nhưng không nằm trong top-5. |
| Why 3 | Tại sao evidence quyết định bị thiếu? | **Giả thuyết:** BM25 ưu tiên đoạn nhiều từ khớp câu hỏi về version, membership và return window; top-5 còn có warranty/product chunks. Thử truy xuất theo hai ý riêng để xem OT-09-P03 có lên hạng không. |
| Why 4 | Tại sao lỗi ngày không được chặn? | **Quan sát trong code:** Prompt yêu cầu giữ exact dates nhưng không bắt buộc tách order date (chọn version) khỏi delivery date (bắt đầu window), cũng không kiểm tra phép tính trước khi xuất answer. |
| Why 5 | Root cause có thể hành động được là gì? | **Giả thuyết cần thử:** Pipeline chưa bảo đảm lấy đủ cặp quy tắc version/ngày bắt đầu và chưa có bước kiểm tra lập luận ngày. Một lần chạy chưa chứng minh phần nào đóng góp nhiều hơn. |

**Root cause từ find_root_cause():**

> Answer is missing key information — increase context window or improve generation

**Đề xuất do Analyzer sinh trong improvement log:**

> Inspect answer claims against the exact retrieved evidence before changing generation prompts or retrieval settings.

**Đối chiếu gợi ý Analyzer với trace:**

> Đồng ý về việc answer thiếu điều kiện quan trọng và tính sai mốc ngày. Gợi ý tăng context window chưa đủ cụ thể: OT-09-P03 vắng mặt, nhưng tăng top-k có thể chỉ thêm nhiễu. Cần thử truy xuất đúng quy tắc trước, rồi kiểm tra model có dùng đúng hai mốc hay không. Kết luận “quá hạn vào October 1” vẫn đúng; sai ở ngày hết hạn September 18 và phần giải thích.

**Proposed fix cụ thể:**

> Với câu hỏi return policy có ngày, truy xuất cả OT-09-P03 và đoạn version tương ứng; yêu cầu answer xác định riêng order date, delivery date, policy version và cửa sổ áp dụng. Kiểm tra H01 và một biến thể mà dùng sai mốc sẽ đảo kết luận: Context Recall phải tăng từ 0.762, Completeness vượt 0.5, và kiểm tra bằng tay rằng 21 ngày được đếm từ September 4, không nêu September 18 là hạn trả hàng.

### Failure 3

**ID và question:**

> H04 — I do not know whether my order was placed before or after the September 1, 2026 return-policy change. Is my opened device definitely eligible for 14 days with a 10% fee, or could the older rule apply?

**Expected answer:**

> The order date is needed to determine the applicable version, so the assistant should not guess. Version 1.0 applies to orders placed before September 1, 2026 and allowed seven calendar days for opened devices with a 15% restocking fee. Version 2.0 applies to orders placed on or after that date and allows 14 days with a 10% fee. Please check or provide the order date so support can identify the applicable rule.

**Actual answer:**

> If your order was placed before September 1, 2026, it falls under Return Policy version 1.0, which allows for a 7-day return period for opened devices with a 15% restocking fee. If your order was placed on or after September 1, 2026, it would be eligible for Return Policy version 2.0, allowing a 14-day return period with a 10% restocking fee. Without knowing the exact order date, both possibilities apply.

**Scores:** Context Recall: 0.800 | Context Precision: 1.000 | Faithfulness: 0.605 | Relevance: 0.536 | Completeness: 0.475 | Overall: 0.539

**Kết quả core:** passed = false | failure_type = off_topic

**Evidence inspection — quan sát trace:** OT-09-P04 có các điều kiện của cả hai versions; OT-09-P05 nói phải nhận diện hai khả năng và hỏi order date khi chưa xác định được version. Cả hai chunks nằm trong top-5 (hạng 1 và 3). Actual answer nêu đủ hai bộ điều kiện nhưng không yêu cầu khách kiểm tra/cung cấp order date.

| Level | Question | Answer |
|---|---|---|
| Symptom | Vấn đề quan sát được là gì? | Answer mô tả hai versions nhưng bỏ bước yêu cầu order date dù OT-09-P05 có trong retrieved contexts; Completeness 0.475. |
| Why 1 | Tại sao symptom xảy ra? | **Quan sát:** Answer lặp lại hai bộ điều kiện đúng nhưng dừng ở “both possibilities apply”; bước yêu cầu khách cung cấp order date bị bỏ. |
| Why 2 | Tại sao không thể quy cho thiếu retrieval? | **Quan sát:** OT-09-P05 nằm hạng 3 và ghi rõ phải hỏi order date khi chưa xác định version. Điều kiện cần đã đến model. |
| Why 3 | Tại sao model vẫn bỏ bước này? | **Giả thuyết:** Prompt chung “Answer every part” không biến hướng dẫn trong chunk thành checklist hành động; model ưu tiên tóm tắt hai versions. Cần thử prompt có bước hỏi dữ kiện còn thiếu. |
| Why 4 | Tại sao thiếu sót chưa được sửa trước khi ghi answer? | **Quan sát trong code:** Pipeline lưu văn bản từ generator trực tiếp; không có kiểm tra riêng cho trường hợp version phụ thuộc order date. Benchmark sau đó phát hiện Completeness 0.475. |
| Why 5 | Root cause có thể hành động được là gì? | **Giả thuyết cần thử:** Thiếu quy tắc hoàn tất câu trả lời có điều kiện: nếu thiếu dữ kiện chọn policy version thì phải nêu cả hai khả năng và hỏi dữ kiện đó. |

**Root cause từ find_root_cause():**

> Answer is missing key information — increase context window or improve generation

**Đề xuất do Analyzer sinh trong improvement log:**

> Compare the user intent with the answer and tighten the prompt or routing for the failing question types.

**Đối chiếu gợi ý Analyzer với trace:**

> Đồng ý rằng answer thiếu thông tin cần thiết. Không đồng ý với nhánh “increase context window” cho H04, vì OT-09-P04 và OT-09-P05 đã được retrieve. Phần cần sửa là tuân theo hướng dẫn yêu cầu order date. Failure type off_topic là nhãn fallback của core khi một answer score dưới 0.5 nhưng không metric nào dưới 0.3; nội dung trả lời vẫn đúng chủ đề.

**Proposed fix cụ thể:**

> Thêm hướng dẫn vào prompt: khi thiếu ngày đặt hàng để chọn version, nêu hai khả năng và hỏi ngày đặt hàng trước khi khẳng định eligibility. Chạy lại H04 và biến thể thiếu ngày; đo Completeness từ mốc 0.475 và đọc answer để xác nhận có câu yêu cầu ngày, giữ đúng 7 ngày/15% và 14 ngày/10%, không khẳng định chắc chắn một version.

---

## 3. Failure Clustering

| Cluster | Root Cause | Failure IDs | Priority |
|---|---|---|---|
| 1 | Giả thuyết: pipeline thiếu kiểm tra có cấu trúc cho chính sách phụ thuộc ngày; H01 thiếu đoạn về mốc đếm, H04 có đoạn yêu cầu hỏi ngày nhưng không dùng. Cần sửa cả coverage lẫn cách hoàn tất answer. | H01, H04 | High |
| 2 | Giả thuyết: câu hỏi ngoài phạm vi chưa được route tới đầy đủ scope evidence và mẫu trả lời theo vai trò OrbitTech. | A01 | High |
| 3 | Giới hạn đo lường: nhãn lexical off_topic không phản ánh đúng nội dung answer; chi tiết bổ sung có trong retrieved chunks nhưng vắng trong gold excerpts. | E04, M03 | Medium |

**Đối chiếu trace cho từng cluster:**

- A01: OT-00-P03 được retrieve; OT-00-P01 có trong gold nhưng vắng khỏi retrieved contexts.
- H01: OT-09-P04 được retrieve; OT-09-P03, quy tắc đếm từ confirmed delivery, vắng khỏi retrieved contexts.
- H04: OT-09-P04 và OT-09-P05 đều được retrieve; answer vẫn không hỏi order date.
- E04: câu bổ sung về remote areas có trong OT-04-P01 đã retrieve, nhưng không có trong gold excerpt.
- M03: phần Packing/carrier interception có trong OT-02-P03 và OT-08-P02 đã retrieve, nhưng không nằm trong gold excerpts.
- E04 và M03 có failure_type off_topic dù actual answers xử lý yêu cầu chính. E04 fail vì Relevance 0.444; M03 fail vì Faithfulness 0.481. Các nhãn này là kết quả ngưỡng của core, chưa phải phán quyết chất lượng từ người chấm.

H01 nằm ở cluster 1 vì câu trả lời về chính sách ngày sai, nhưng riêng H01 còn có retrieval gap. Việc thêm checklist generation mà không đưa OT-09-P03 vào context có thể chưa sửa được case đó. Cluster 3 là công việc hiệu chuẩn đánh giá; không nên sửa answer tốt chỉ để khớp từ với reference.

**Nếu chỉ được sửa một cluster, bạn chọn cluster nào và vì sao?**

> Tôi chọn cluster 1 vì hai hard cases liên quan đến điều kiện chính sách theo ngày. H01 nêu sai ngày kết thúc dù kết luận quá hạn đúng; trong một câu hỏi gần ranh giới, cùng lỗi này có thể đảo kết luận. H04 không hỏi ngày đặt hàng nên khách chưa biết version nào áp dụng. Tôi sẽ đo riêng việc truy xuất OT-09-P03/OT-09-P05 và việc answer dùng chúng, tránh coi một score trung bình tăng là đủ chứng minh hai lỗi đã hết.

---

## 4. Improvement Log

Bảng copy nguyên dạng từ failure_analysis.improvement_log trong artifacts/benchmark_results.json. Failure ID chính là QA ID.

| Failure ID | Type | Root Cause | Suggested Fix | Status |
|------------|------|------------|---------------|--------|
| E04 | off_topic | Answer does not address the question — improve prompt clarity | Add intent detection or a clarification step for ambiguous requests, and test that the response stays on the requested topic. | Open |
| M03 | off_topic | Context is missing or irrelevant — improve retrieval | Trace unsupported claims to their retrieved chunks; improve evidence filtering and require answers to omit claims the context does not support. | Open |
| H01 | off_topic | Answer is missing key information — increase context window or improve generation | Inspect answer claims against the exact retrieved evidence before changing generation prompts or retrieval settings. | Open |
| H04 | off_topic | Answer is missing key information — increase context window or improve generation | Compare the user intent with the answer and tighten the prompt or routing for the failing question types. | Open |
| A01 | hallucination | Context is missing or irrelevant — improve retrieval | Compare missing answer points with the expected answer and verify that the needed evidence fits in the generator context. | Open |

**Ba improvement suggestions ưu tiên sau khi đối chiếu bảng máy sinh với trace:**

1. Với câu hỏi về phiên bản return policy, lấy đủ quy tắc chọn version và mốc đếm ngày, rồi yêu cầu answer nêu các mốc riêng và hỏi order date khi thiếu (H01, H04).
2. Route yêu cầu ngoài phạm vi đến OT-00-P01/P03 và buộc phản hồi giải thích vai trò, nêu chủ đề OrbitTech được hỗ trợ (A01).
3. Human review các nhãn E04/M03; mở rộng gold evidence khi một chi tiết đúng được retrieved nhưng chưa có trong reference, và báo cáo thêm đánh giá ngữ nghĩa bên cạnh word overlap.

| Suggestion | Target metric | Verification method |
|---|---|---|
| Bổ sung cặp quy tắc thời gian và checklist trả lời policy (H01, H04) | H01 Context Recall 0.762 và Completeness 0.429; H04 Completeness 0.475 | Chạy cùng 20 questions sau thay đổi, so với baseline đã lưu; xác nhận H01 retrieve OT-09-P03 và đếm từ delivery, H04 hỏi order date. Đọc actual answers và chunks, không chỉ nhìn trung bình. |
| Route ngoài phạm vi và hướng dẫn từ chối theo corpus (A01) | A01 Context Recall 0.533; Faithfulness 0.071; Completeness 0.133 | Chạy A01 cùng vài cách hỏi tương tự; xác nhận scope chunks xuất hiện, answer không chẩn đoán, nêu vai trò và ví dụ chủ đề hỗ trợ. So từng score với baseline và kiểm tra claim thủ công. |
| Hiệu chuẩn gold/metric cho cases có answer đúng nhưng bị gắn off_topic (E04, M03) | E04 Relevance 0.444; M03 Faithfulness 0.481; độ đồng thuận giữa nhãn máy và người chấm | Hai người đọc question, answer, gold và retrieved chunks độc lập. Chỉ bổ sung gold excerpt khi corpus hỗ trợ, giữ 20 IDs; chạy lại evaluator trên actual answers đã lưu và lập baseline mới cho phiên bản gold/metric mới. |

Suggestions do generate_improvement_suggestions() sinh, theo thứ tự artifact:

1. Add intent detection or a clarification step for ambiguous requests, and test that the response stays on the requested topic.
2. Trace unsupported claims to their retrieved chunks; improve evidence filtering and require answers to omit claims the context does not support.
3. Inspect answer claims against the exact retrieved evidence before changing generation prompts or retrieval settings.
4. Compare the user intent with the answer and tighten the prompt or routing for the failing question types.
5. Compare missing answer points with the expected answer and verify that the needed evidence fits in the generator context.

---

## 5. Regression Testing Strategy

Contract của run_regression() đánh dấu regression khi một answer metric trung bình mới giảm hơn 0.05 so với baseline. Đây là so sánh giữa hai lần chạy, không phải pass rule của một QA (mỗi answer score cần từ 0.5 trở lên).

**Câu 1: Khi nào chạy run_regression() trong production workflow?**

> Chạy offline trước khi merge hoặc release mỗi thay đổi prompt, model, retriever, chunking hoặc corpus. Dùng cùng 20 QA có ID và expected evidence cố định để so lần sinh answer mới với baseline đã duyệt; lưu thêm answer và chunk trace để giải thích chênh lệch. Khi chỉ sửa evaluator, chạy lại evaluate_answers.py trên actual_answers.json đã lưu để cô lập tác động của phép đo, rồi so với baseline dùng cùng phiên bản dataset. Nếu corpus hoặc golden evidence đổi, validate và review version mới trước khi thiết lập baseline tương ứng; không so hai bộ câu hỏi/reference khác nhau như thể chúng là cùng một benchmark.

**Câu 2: Threshold drop 0.05 có phù hợp OrbitTech Customer Support không? Vì sao?**

> Mức giảm hơn 0.05 là tín hiệu regression hữu ích cho ba answer metric trung bình; giảm đúng 0.05 không bị hàm đánh dấu. Tôi giữ nguyên contract trong code. Với 20 cases, điểm trung bình có thể che một lỗi nghiêm trọng ở một câu chính sách hoặc privacy nếu các câu khác tốt lên, còn word overlap có nhiễu từ cách diễn đạt. Vì vậy dùng thêm kiểm tra từng case rủi ro cao và đọc trace; không xem kết quả passed của run_regression() là giấy phép phát hành duy nhất.

**Câu 3: Metric/failure nào phải block deployment, metric nào chỉ alert?**

> Đề xuất block khi run_regression() báo giảm hơn 0.05 ở Faithfulness, Relevance hoặc Completeness; khi benchmark thấp hơn ngưỡng release đã đề xuất ở Exercise 1.3 (trung bình Faithfulness 0.85, Relevance 0.75, Completeness 0.75); hoặc khi human review xác nhận claim sai về ngày áp dụng chính sách, hoàn tiền, bảo mật hay dữ liệu riêng tư. Theo ngưỡng tuyệt đối đó, lần chạy hiện tại 0.658/0.635/0.688 chưa đủ điều kiện production, dù Lab vẫn giữ kết quả thật để phân tích. Context Recall và Precision trung bình giảm thì alert và kiểm tra chunks; nếu thiếu evidence làm hỏng case rủi ro cao, chặn theo lỗi case cụ thể. Nhãn off_topic lexical đơn lẻ như E04/M03 cần human review trước khi chặn.

**Câu 4: Điền evaluation stages vào flow.**

Code/prompt/retrieval change → [Validate dataset và IDs] → [Offline benchmark, lưu answer/chunk trace] → [run_regression(), quality gate và human review] → Deploy

> So sánh trên cùng golden dataset và phiên bản corpus được ghi nhận. Thay đổi evaluator thì tái chấm actual answers đã lưu; thay đổi generator/retriever thì sinh artifact mới rồi đánh giá. Nếu gate fail, điều tra theo QA ID và retrieved chunks, sửa nguyên nhân và chạy lại trước release. Sau deploy, theo dõi mẫu traffic thật và đưa failures mới vào vòng đánh giá kế tiếp.

---

## 6. Continuous Improvement Loop

Evaluate → Analyze → Improve → Augment benchmark → Repeat

| Priority | Action | Metric dự kiến cải thiện | Expected impact |
|---:|---|---|---|
| 1 | Lấy đủ policy trigger/counting evidence và kiểm tra mốc ngày trong answer của H01/H04. | Context Recall H01; Completeness H01/H04; kiểm tra đúng điều kiện theo human review. | Giảm nguy cơ giải thích sai cửa sổ trả hàng hoặc bỏ bước hỏi order date. |
| 2 | Route A01 đến scope evidence và hướng dẫn phản hồi ngoài phạm vi theo OT-00. | Context Recall, Faithfulness, Completeness của A01. | Từ chối yêu cầu y tế đúng vai trò và dẫn khách về phạm vi hỗ trợ OrbitTech. |
| 3 | So nhãn E04/M03 với đánh giá người chấm, rà soát gold excerpts và hiệu chuẩn metric. | Độ đồng thuận nhãn; chẩn đoán Relevance E04 và Faithfulness M03. | Giảm false positive, giúp nhóm sửa đúng lỗi của hệ thống thay vì tối ưu theo từ khóa. |

**Hai hoặc ba failure cases nào cần thêm vào benchmark ở vòng tiếp theo?**

> (1) Đơn chưa mở đặt ngày August 31, nhận ngày September 10, hỏi ngày September 25 có còn được trả không: cách đếm sai từ order date sẽ đảo kết luận. (2) Một câu ngoài phạm vi dùng từ “symptoms” và “diagnosis” dễ khớp nhầm tài liệu repair, để kiểm tra route scope và cách từ chối. (3) Khách không biết ngày đặt hàng nhưng hỏi đồng thời về mức phí mở hộp và lợi ích OrbitPlus đã kích hoạt sau checkout: answer cần nêu các khả năng và hỏi ngày đặt hàng, không hứa lợi ích hồi tố. Ba case này là đề xuất cho vòng sau; golden_dataset.json nộp hiện tại vẫn giữ đúng 20 slots.

---

## 7. Final Reflection

**Điều gì trong kết quả benchmark trái với dự đoán ban đầu của bạn?**

> Tôi dự đoán Context Precision gần 0.966 sẽ đi kèm câu trả lời chính sách đủ chắc, nhưng H01 vẫn thiếu OT-09-P03 và nêu sai mốc kết thúc, còn H04 đã có OT-09-P05 mà vẫn không hỏi ngày đặt hàng. Tôi cũng không dự đoán E04 bị gắn off_topic: answer nêu đúng thời gian vận chuyển và một chi tiết remote areas có trong chunk đã retrieve. Những trường hợp này nhắc tôi xem từng QA và evidence trước khi quyết định sửa retrieval, prompt hay phép đo.

**Word-overlap heuristics trong lab có giới hạn gì? Nếu đưa hệ thống vào production, bạn sẽ thay hoặc bổ sung metric nào?**

> Word overlap không kiểm tra được quan hệ “order date chọn version, delivery date bắt đầu đếm ngày”: H01 kết luận quá hạn đúng nhưng giải thích deadline sai. Nó cũng không hiểu E04 trả lời đúng ý dù Relevance 0.444, hoặc M03 thêm điều kiện Packing/interception có trong retrieved chunks nhưng ngoài gold excerpt nên Faithfulness giảm. A01 bị gắn hallucination do overlap thấp dù đã từ chối chẩn đoán. Với production, tôi sẽ bổ sung kiểm tra claim theo evidence/citation, phép kiểm chính sách theo điều kiện và ngày, đánh giá ngữ nghĩa hoặc human labels đã hiệu chuẩn cho relevance/completeness. Các case an toàn, privacy và policy phiên bản cần human review định kỳ; không thay toàn bộ quyết định bằng một điểm trung bình.

---

## 8. Bonus — Điều rút ra từ hai bài mở rộng

Exercise 3.4 trong exercises.md là **thiết kế so sánh** Ragas và DeepEval
trên cùng 20 actual answers/chunks đã lưu. Hai framework chưa chạy judge,
nên chưa có scores để kết luận bên nào strict hơn hoặc có tìm cùng failure
IDs hay không. Khi triển khai, cần giữ cùng model chấm, rubric và baseline,
rồi adjudicate các bất đồng với gold evidence và người chấm.

Exercise 3.5 đã chạy bằng bonus_reranking.py; chi tiết 20 IDs và thứ tự
chunks nằm trong artifacts/bonus_reranking.json. Rerank dùng question,
không dùng expected answer để xếp hạng. Context Recall trung bình giữ nguyên
0.85977; Context Precision giảm nhẹ từ 0.96632 xuống 0.95694 (3 cases tăng,
15 không đổi, 2 giảm). H01 không đổi vì OT-09-P03 vốn không được retrieve;
đây là bằng chứng cụ thể rằng sửa thứ hạng không thay thế việc bổ sung
evidence. A01 giảm Precision mạnh do ngưỡng overlap xem một số chunk repair
là liên quan dù chúng không thích hợp cho câu hỏi y tế. Tôi sẽ dùng các
kết quả này để ưu tiên sửa retrieval coverage và hiệu chuẩn metric trước
khi coi lexical reranker là cải tiến cho sản phẩm.
