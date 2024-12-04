import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import io
import base64

class DispatchingRulesProcessor:
    def load_data(self, file):
        try:
            return pd.read_excel(file, sheet_name='Input')
        except Exception as e:
            raise ValueError(f"Error loading file: {str(e)}")

    def _base64_encode_image(self, fig):
        # Convert plot to base64 encoded image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.getbuffer()).decode('ascii')

    def execute_rules(self, Input, rules):
        results = {}
        gantt_data = {}
        for rule in rules:
            if rule == "SPT":
                results[rule] = self._spt_logic(Input)
            elif rule == "LPT":
                results[rule] = self._lpt_logic(Input)
            elif rule == "WSPT":
                results[rule] = self._wspt_logic(Input)
            elif rule == "EDD":
                results[rule] = self._edd_logic(Input)
            elif rule == "SRPT":
                results[rule], gantt_data[rule] = self._srpt_logic(Input)
            elif rule == "LST":
                results[rule], gantt_data[rule] = self._lst_logic(Input)
            elif rule == "LRPT":
                results[rule], gantt_data[rule] = self._lrpt_logic(Input)

        return results, gantt_data

    def _spt_logic(self, Input):
        plan = Input.sort_values(by='pj')
        return self._calculate_schedule(plan)

    def _lpt_logic(self, Input):
        plan = Input.sort_values(by='pj', ascending=False)
        return self._calculate_schedule(plan)

    def _wspt_logic(self, Input):
        # Weighted Shortest Processing Time (WSPT) logic
        Input['cj'] = Input['pj'] / Input['wj'] # Calculate weight for each job
        plan = Input.sort_values(by='cj')
        return self._calculate_schedule(plan)

    def _edd_logic(self, Input):
        plan = Input.sort_values(by='dj')
        return self._calculate_schedule(plan)


    def _lst_logic(self, Input):
        # Check for required columns
        required_columns = ['job', 'pj', 'dj', 'rj']
        if not all(col in Input.columns for col in required_columns):
            raise ValueError(f"Input data must contain columns: {', '.join(required_columns)}")
        
        # Filter input DataFrame for required columns
        Input = Input[required_columns].copy()

        # Initialize variables
        n = len(Input)
        remaining_time = Input['pj'].tolist()
        current_time = 0
        gantt_data = []
        plan = []

        while True:
            # Calculate slack time for each job that has been released
            slack_times = []
            for i in range(n):
                if remaining_time[i] > 0 and Input['rj'].iloc[i] <= current_time:
                    due_date = Input['dj'].iloc[i]
                    slack_time = due_date - current_time - remaining_time[i]
                    slack_times.append((slack_time, i))
            
            if not slack_times:
                # No jobs available, move time forward to the next job's release
                next_job_times = [Input['rj'].iloc[i] for i in range(n) if remaining_time[i] > 0]
                if next_job_times:
                    current_time = min(next_job_times)  # Move time forward
                    continue
                else:
                    break  # Exit if no jobs left
            
            # Find the job with the least slack time
            least_slack_job_index = min(slack_times, key=lambda x: x[0])[1]
            least_slack_job_time = remaining_time[least_slack_job_index]

            # Execute the job for one time unit
            remaining_time[least_slack_job_index] -= 1
            current_time += 1

            # Record Gantt chart data
            gantt_data.append((Input['job'].iloc[least_slack_job_index], current_time - 1, current_time))

            # If the job is completed
            if remaining_time[least_slack_job_index] == 0:
                flow_time = current_time - Input['rj'].iloc[least_slack_job_index]
                # Set Flow time to 'N/A' if negative
                flow_time_display = flow_time if flow_time >= 0 else 'N/A'
                plan.append({
                    'job': Input['job'].iloc[least_slack_job_index],
                    'rj': Input['rj'].iloc[least_slack_job_index],
                    'pj': Input['pj'].iloc[least_slack_job_index],
                    'Start time': current_time - least_slack_job_time,
                    'Completion time': current_time,
                    'Flow time': flow_time_display,
                    'Late time': max(0, current_time - Input['dj'].iloc[least_slack_job_index])
                })

        return pd.DataFrame(plan), gantt_data

    def _srpt_logic(self, Input):
        # Kiểm tra dữ liệu đầu vào có đủ cột không
        required_columns = ['job', 'pj', 'dj', 'rj']
        if not all(col in Input.columns for col in required_columns):
            raise ValueError(f"Input data must contain columns: {', '.join(required_columns)}")
        
        # Lọc dữ liệu chỉ gồm các cột cần thiết
        Input = Input[required_columns].copy()
        
        n = len(Input)  # Số lượng tiến trình

        # Khởi tạo các biến
        completion_time = [0] * n
        start_time = [None] * n  # Thêm mảng lưu Start time
        remaining_time = Input['pj'].tolist()
        current_time = 0
        gantt_data = []  # Danh sách dữ liệu cho biểu đồ Gantt
        plan = []
        # Biến lưu trạng thái Input
        plan = Input.copy()
        plan['Completion time'] = 0
        plan['Start time'] = None  # Thêm cột Start time
        plan['Completion time'] = None  # Thêm cột Completion time
        plan['Flow time'] = None # Thêm cột Flow time

        while True:
            # Tìm tiến trình có thời gian thực hiện còn lại ngắn nhất và đã đến
            min_remaining_time = float("inf")
            shortest_process_index = None

            for i in range(n):
                if plan.iloc[i]['rj'] <= current_time and remaining_time[i] < min_remaining_time and remaining_time[i] > 0:
                    min_remaining_time = remaining_time[i]
                    shortest_process_index = i

            if shortest_process_index is None:
                # Tăng thời gian nếu không có tiến trình nào khả dụng
                if all(rt == 0 for rt in remaining_time):
                    break
                current_time += 1
                continue

            # Ghi nhận Start time nếu chưa được thiết lập
            if start_time[shortest_process_index] is None:
                start_time[shortest_process_index] = current_time

            # Thực hiện tiến trình ngắn nhất
            current_time += 1
            remaining_time[shortest_process_index] -= 1

            # Kiểm tra xem tiến trình đã hoàn thành chưa
            if remaining_time[shortest_process_index] == 0:
                completion_time[shortest_process_index] = current_time
                plan.at[shortest_process_index, 'Completion time'] = current_time

            # Lưu dữ liệu cho biểu đồ Gantt
            gantt_data.append([plan.iloc[shortest_process_index]['job'], current_time - 1, current_time])

        # Cập nhật Completion Time, Start Time, và tính toán Late Time
        plan['Completion time'] = completion_time
        plan['Start time'] = start_time
        plan['Late time'] = plan['Completion time'] - plan['dj']
        plan['Late time'] = plan['Late time'].clip(lower=0)  # Không có thời gian trễ âm
        plan['Flow time'] = plan['Completion time'] - plan['rj']
        plan['Flow time'] = plan['Flow time'].apply(lambda x: x if x >= 0 else 'N/A')

        # Sắp xếp theo Completion time để tạo kết quả
        plan = plan.sort_values(by='Completion time', ascending=True)

        return pd.DataFrame(plan), gantt_data

    def _lrpt_logic(self, Input):
        # Kiểm tra dữ liệu đầu vào có đủ cột không
        required_columns = ['job', 'pj', 'dj', 'rj']
        if not all(col in Input.columns for col in required_columns):
            raise ValueError(f"Input data must contain columns: {', '.join(required_columns)}")
        
        # Lọc dữ liệu chỉ gồm các cột cần thiết
        Input = Input[required_columns].copy()
        
        n = len(Input)  # Số lượng tiến trình

        # Khởi tạo các biến
        completion_time = [0] * n
        start_time = [None] * n  # Mảng lưu Start time
        remaining_time = Input['pj'].tolist()
        current_time = 0
        gantt_data = []  # Danh sách dữ liệu cho biểu đồ Gantt
        plan = Input.copy()
        plan['Completion time'] = [None] * n  # Thêm cột Completion time
        plan['Start time'] = [None] * n  # Thêm cột Start time
        plan['Flow time'] = [None] * n  # Thêm cột Flow time
        completed_jobs = 0
        while completed_jobs < n:
            # Tìm tiến trình có thời gian thực hiện còn lại dài nhất và đã đến
            max_remaining_time = float("-inf")
            longest_process_index = None

            for i in range(n):
                if plan.iloc[i]['rj'] <= current_time and remaining_time[i] > max_remaining_time:
                    max_remaining_time = remaining_time[i]
                    longest_process_index = i

            if longest_process_index is None:
                # Không có tiến trình khả dụng, tăng thời gian nhanh chóng đến tiến trình tiếp theo
                next_available_time = min([plan.iloc[i]['rj'] for i in range(n) if remaining_time[i] > 0])
                current_time = max(current_time + 1, next_available_time)
                continue

            # Ghi nhận Start time nếu chưa được thiết lập
            if start_time[longest_process_index] is None:
                start_time[longest_process_index] = current_time

            # Thực hiện tiến trình dài nhất
            current_time += 1
            remaining_time[longest_process_index] -= 1

            # Kiểm tra xem tiến trình đã hoàn thành chưa
            if remaining_time[longest_process_index] == 0:
                completion_time[longest_process_index] = current_time
                plan.at[longest_process_index, 'Completion time'] = current_time
                completed_jobs += 1


            # Lưu dữ liệu cho biểu đồ Gantt
            gantt_data.append([plan.iloc[longest_process_index]['job'], current_time - 1, current_time])

        # Cập nhật Completion Time, Start Time, và tính toán Late Time
        plan['Completion time'] = completion_time
        plan['Start time'] = start_time
        plan['Late time'] = plan['Completion time'] - plan['dj']
        plan['Late time'] = plan['Late time'].clip(lower=0)  # Không có thời gian trễ âm
        plan['Flow time'] = plan['Completion time'] - plan['rj']
        plan['Flow time'] = plan['Flow time'].apply(lambda x: x if x >= 0 else 'N/A')

        # Sắp xếp theo Completion time để tạo kết quả
        plan = plan.sort_values(by='Completion time', ascending=True)

        return pd.DataFrame(plan), gantt_data

    def _calculate_schedule(self, plan):
        current_time = 0
        sequence = []

        for index, row in plan.iterrows():
            start_time = current_time
            completion_time = start_time + row['pj']
            flow_time = completion_time - row['rj']
            late_time = max(0, completion_time - row['dj'])

            # Set Flow time to 'N/A' if negative
            flow_time_display = flow_time if flow_time >= 0 else 'N/A'

            sequence.append({
                'job': row['job'],
                'rj': row['rj'],
                'pj': row['pj'],
                'Start time': start_time,
                'Completion time': completion_time,
                'Flow time': flow_time_display,
                'Late time': late_time
            })

            current_time += row['pj']  # Update current time

        return pd.DataFrame(sequence)

    def _generate_plot_gantt(self, plan, rule):
        fig, ax = plt.subplots(figsize=(10, 3))

        for i in range(len(plan)):
            task = plan['job'].iloc[i]
            start_time = plan['Start time'].iloc[i]
            duration = plan['pj'].iloc[i]
            ax.barh(y=task, width=duration, left=start_time, color='#FF6666')

        plt.title(f'Gantt chart for {rule}', fontsize=12, fontweight='bold')
        plt.xlabel('Time (days)', fontweight='bold')
        plt.ylabel('Jobs', fontweight='bold')
        plt.xticks(range(0, int(plan['Completion time'].max()) + 2, 2))

        # Convert plot to base64 image
        plt.tight_layout()
        base64_image = self._base64_encode_image(fig)
        plt.close(fig)
        return base64_image

    def _generate_plot_gantt_with_preemption(self, gantt_data, rule):
        fig, ax = plt.subplots(figsize=(10, 3))
        for data in gantt_data:
            task, start_time, end_time = data
            # Ensure start_time and end_time are numeric
            start_time = float(start_time)
            end_time = float(end_time)
            ax.barh(y=task, width=(end_time - start_time), left=start_time, color='#FF6666')

        plt.title(f'Gantt chart for {rule}', fontsize=12, fontweight='bold')
        plt.xlabel('Time (days)', fontweight='bold')
        plt.ylabel('Jobs', fontweight='bold')

        # Convert plot to base64
        plt.tight_layout()
        base64_image = self._base64_encode_image(fig)
        plt.close(fig)
        return base64_image

    def compare_rules(self, rules):
        comparison_data = []
        for rule, plan in rules.items():
            avg_completion_time = plan['Completion time'].mean()

            # Check if there is any 'N/A' in Flow time
            if (plan['Flow time'] == 'N/A').any():
                avg_flow_time = 'N/A'
            else:
                avg_flow_time = plan['Flow time'].mean()

            avg_late_time = plan['Late time'].mean()
            utilization = plan['pj'].sum() * 100 / plan['Completion time'].sum()

            comparison_data.append({
                'Rule': rule,
                'Average Completion Time': f"{avg_completion_time:.2f}" if isinstance(avg_completion_time, (int, float)) else "N/A",
                'Average Flow Time': f"{avg_flow_time:.2f}" if isinstance(avg_flow_time, (int, float)) else avg_flow_time,
                'Average Late Time': f"{avg_late_time:.2f}" if isinstance(avg_late_time, (int, float)) else "N/A",
                'Utilization (%)': f"{utilization:.2f}" if isinstance(utilization, (int, float)) else "N/A"
            })

        return comparison_data

# Flask Application
app = Flask(__name__)
CORS(app)
processor = DispatchingRulesProcessor()

@app.route('/process', methods=['POST'])
def process_file():
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Check file type
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "Invalid file type. Please upload an Excel file"}), 400
        
        # Load data
        Input = processor.load_data(file)
        
        # Get mode and rules
        mode = request.form.get('mode', 'execute')
        rules = request.form.getlist('rules')
        
        # Validate rules
        valid_rules = ["SPT", "LPT", "WSPT", "EDD", "SRPT", "LST", "LRPT"]
        if not all(rule in valid_rules for rule in rules):
            return jsonify({"error": "Invalid rules selected"}), 400
        
        # if mode == 'execute':
        # Execute selected rules
        results, gantt_data = processor.execute_rules(Input, rules)
        # Convert DataFrames to dictionaries with embedded Gantt charts
        serializable_results = []
        for rule, plan in results.items():
            if rule == 'SRPT' or rule == 'LST' or rule == 'LRPT':
                serializable_results.append({
                    'rule': rule,
                    'schedule': plan.to_dict(orient='records'),
                    'gantt_chart': processor._generate_plot_gantt_with_preemption(gantt_data[rule], rule)
                })
            else:
                serializable_results.append({
                    'rule': rule,
                    'schedule': plan.to_dict(orient='records'),
                    'gantt_chart': processor._generate_plot_gantt(plan, rule)
                })

        if mode == 'compare':
            # Execute rules for comparison
            results, _ = processor.execute_rules(Input, rules)
            comparison_data = processor.compare_rules(results)
            return jsonify({
                "results": serializable_results,
                "compare_data": comparison_data
            })
        elif mode == 'execute':
            return jsonify({
                "results": serializable_results,
            })

        else:
            return jsonify({"error": "Invalid mode"}), 400
    
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred" + repr(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
