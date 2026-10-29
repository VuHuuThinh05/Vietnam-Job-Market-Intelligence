# Kiểm tra dữ liệu nguồn — VietJobs (Source Audit)

## 1. Nguồn và phạm vi

| Nội dung | Thông tin |
| --- | --- |
| Bộ dữ liệu | VietJobs |
| Nguồn tải | [Hugging Face — VietJobs](https://huggingface.co/datasets/dinhieufam/VietJobs) |
| Dự án nguồn | [VinNLP / VietJobs](https://github.com/VinNLP/VietJobs) |
| File sử dụng | `data/raw/external/VietJobs.csv` |
| Dữ liệu đã nạp và đối chiếu trong môi trường phát triển | **48.092 bản ghi, 18 cột, 16 nhóm ngành** |
| Phạm vi | Dữ liệu tuyển dụng lịch sử; không phải dữ liệu live |

File CSV không được commit do kích thước và điều kiện sử dụng dữ liệu. Bản quyền / quyền phân phối lại cần được xác minh riêng, không suy từ license của mã nguồn.

## 2. Kiểm tra đã thực hiện

| Hạng mục | Kết quả / bằng chứng | Trạng thái |
| --- | --- | --- |
| Cấu trúc CSV | `load_vietjobs.py` kiểm tra thứ tự tên 18 cột và số trường mỗi dòng | Có triển khai |
| Số dòng | Đã đối chiếu **48.092** bản ghi trong PostgreSQL ở môi trường phát triển | Đã xác minh khi chạy local |
| Số nhóm ngành | `COUNT(DISTINCT category) = 16` trong dữ liệu raw | Đã xác minh khi chạy local |
| Giá trị thiếu | Đã phân tích qua `profile_dataset.py` và các script kiểm tra nguồn | Đã khảo sát |
| Bất thường lương | Đã phát hiện trường hợp min > max và trường hợp 0/0 không phải “Thoả thuận” | Đã khảo sát |
| IT subset | Có script `profile_it_subset.py` và `inspect_it_skills.py` | Đã khảo sát phụ trợ |
| Bản ghi trùng lặp | Có lưu ý về rủi ro đếm trùng; chưa đủ kết quả xác minh để khẳng định tỷ lệ | Chưa kết luận |
| Nguồn cập nhật theo lịch | Chưa tích hợp | Không áp dụng hiện tại |
| Quyền phân phối dữ liệu | Chưa có xác nhận giấy phép dữ liệu | Cần xác minh |

**Phân biệt:** “Có triển khai” mô tả tính năng trong source code; “Đã xác minh khi chạy local” dựa trên kết quả chạy trước đây, không phải một lần chạy CI mới trên GitHub.

## 3. Các vấn đề dữ liệu đáng chú ý

Kết quả profiling đã ghi nhận tỷ lệ thiếu ở một số trường:

| Trường | Số bản ghi thiếu | Tỷ lệ |
| --- | ---: | ---: |
| `languages_required` | 35.796 | 74,43% |
| `technical_skills` | 6.437 | 13,38% |
| `working_hours` | 4.982 | 10,36% |
| `soft_skills` | 2.641 | 5,49% |
| `qualifications` | 1.221 | 2,54% |

Có ghi nhận **2 bản ghi** có `salary_min > salary_max`, và **3 bản ghi** min/max bằng 0 nhưng không được ghi “Thoả thuận”. Những trường hợp này cần được xử lý cẩn trọng khi đọc các số liệu lương.

**Quy ước nghiệp vụ:** một số chuỗi rỗng hoặc giá trị `0` trong trường yêu cầu có thể mang nghĩa “không yêu cầu”; không nên coi mọi trường hợp đó là lỗi dữ liệu. Mức lương “Thoả thuận” cũng không có nghĩa là mức lương thực bằng 0.

## 4. Các script phục vụ kiểm tra

| File | Mục đích |
| --- | --- |
| `src/validation/profile_dataset.py` | Thống kê và profiling toàn dataset |
| `src/validation/inspect_source_data.py` | Khảo sát cấu trúc và giá trị nguồn |
| `src/validation/inspect_salary_anomalies.py` | Kiểm tra bất thường mức lương |
| `src/validation/inspect_special_values.py` | Khảo sát giá trị rỗng, 0, “Thoả thuận” |
| `src/validation/inspect_it_skills.py` | Khảo sát kỹ năng trong nhóm IT |
| `src/validation/profile_it_subset.py` | Profiling tập con IT |

Các script này là công cụ **khảo sát độc lập**; DAG `vietjobs_pipeline` chỉ có ba task `ingest_vietjobs → dbt_run → dbt_test`.

## 5. Hạn chế và kết luận

- Không suy diễn số liệu từ CSV lịch sử thành xu hướng tuyển dụng hiện tại.
- Không khẳng định dữ liệu đã được loại bỏ bản ghi trùng khi chưa xác minh.
- Không công khai CSV gốc trước khi làm rõ quyền phân phối lại.
- Khi phân tích lương, dùng điều kiện lọc khoảng lương hợp lệ để tránh đưa giá trị thỏa thuận hoặc bất thường vào phép tính.

Nhìn chung, dataset phù hợp để **xây dựng và minh họa pipeline Data Engineering**, nhưng chưa đủ để làm hệ thống theo dõi thị trường tuyển dụng trực tiếp.
