#!/usr/bin/env python3
"""
Comix Server 성능 및 로드 테스트

서버의 성능 특성과 부하 처리 능력을 테스트합니다.
"""

import asyncio
import concurrent.futures
import json
import statistics
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import psutil
import requests
from dataclasses import dataclass, asdict


@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    response_time: float
    status_code: int
    content_length: int
    error: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class LoadTestResult:
    """로드 테스트 결과 데이터 클래스"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    total_duration: float
    error_rate: float
    throughput_mb_per_sec: float


class PerformanceTester:
    """성능 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:31257"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def single_request_test(self, endpoint: str, timeout: float = 10.0) -> PerformanceMetrics:
        """단일 요청 성능 테스트"""
        start_time = time.time()
        
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            content_length = len(response.content) if response.content else 0
            
            return PerformanceMetrics(
                response_time=response_time,
                status_code=response.status_code,
                content_length=content_length,
                timestamp=start_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return PerformanceMetrics(
                response_time=response_time,
                status_code=0,
                content_length=0,
                error=str(e),
                timestamp=start_time
            )
    
    def concurrent_load_test(
        self,
        endpoint: str,
        num_requests: int,
        concurrency: int,
        timeout: float = 10.0
    ) -> LoadTestResult:
        """동시 요청 로드 테스트"""
        
        def make_request() -> PerformanceMetrics:
            return self.single_request_test(endpoint, timeout)
        
        start_time = time.time()
        metrics: List[PerformanceMetrics] = []
        
        # ThreadPoolExecutor를 사용한 동시 요청
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    metric = future.result()
                    metrics.append(metric)
                except Exception as e:
                    metrics.append(PerformanceMetrics(
                        response_time=0.0,
                        status_code=0,
                        content_length=0,
                        error=str(e)
                    ))
        
        total_duration = time.time() - start_time
        
        return self._calculate_load_test_result(metrics, total_duration)
    
    def sustained_load_test(
        self,
        endpoint: str,
        duration_seconds: int,
        requests_per_second: int
    ) -> LoadTestResult:
        """지속적인 부하 테스트"""
        
        metrics: List[PerformanceMetrics] = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        request_interval = 1.0 / requests_per_second
        
        def make_requests():
            last_request_time = time.time()
            
            while time.time() < end_time:
                current_time = time.time()
                
                # 요청 간격 조절
                if current_time - last_request_time >= request_interval:
                    metric = self.single_request_test(endpoint, timeout=5.0)
                    metrics.append(metric)
                    last_request_time = current_time
                else:
                    time.sleep(0.001)  # 1ms 대기
        
        # 별도 스레드에서 요청 실행
        thread = threading.Thread(target=make_requests)
        thread.start()
        thread.join()
        
        actual_duration = time.time() - start_time
        
        return self._calculate_load_test_result(metrics, actual_duration)
    
    def memory_stress_test(
        self,
        large_image_endpoint: str,
        num_concurrent_downloads: int,
        timeout: float = 30.0
    ) -> Dict[str, any]:
        """메모리 스트레스 테스트 (큰 이미지 동시 다운로드)"""
        
        def download_large_image() -> Tuple[PerformanceMetrics, int]:
            """큰 이미지 다운로드 및 메모리 사용량 측정"""
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            metric = self.single_request_test(large_image_endpoint, timeout)
            
            final_memory = process.memory_info().rss
            memory_used = final_memory - initial_memory
            
            return metric, memory_used
        
        start_time = time.time()
        results = []
        memory_usage = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_downloads) as executor:
            futures = [executor.submit(download_large_image) for _ in range(num_concurrent_downloads)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    metric, memory_used = future.result()
                    results.append(metric)
                    memory_usage.append(memory_used)
                except Exception as e:
                    results.append(PerformanceMetrics(
                        response_time=0.0,
                        status_code=0,
                        content_length=0,
                        error=str(e)
                    ))
                    memory_usage.append(0)
        
        total_duration = time.time() - start_time
        
        return {
            'load_test_result': self._calculate_load_test_result(results, total_duration),
            'memory_metrics': {
                'total_memory_used': sum(memory_usage),
                'average_memory_per_request': statistics.mean(memory_usage) if memory_usage else 0,
                'max_memory_per_request': max(memory_usage) if memory_usage else 0,
                'memory_efficiency': sum(r.content_length for r in results) / max(sum(memory_usage), 1)
            }
        }
    
    def _calculate_load_test_result(
        self,
        metrics: List[PerformanceMetrics],
        total_duration: float
    ) -> LoadTestResult:
        """로드 테스트 결과 계산"""
        
        if not metrics:
            return LoadTestResult(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                requests_per_second=0.0,
                total_duration=total_duration,
                error_rate=1.0,
                throughput_mb_per_sec=0.0
            )
        
        successful_metrics = [m for m in metrics if m.error is None and m.status_code == 200]
        failed_metrics = [m for m in metrics if m.error is not None or m.status_code != 200]
        
        response_times = [m.response_time for m in successful_metrics]
        content_lengths = [m.content_length for m in successful_metrics]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else avg_response_time
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 1 else avg_response_time
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0.0
        
        total_bytes = sum(content_lengths)
        throughput_mb_per_sec = (total_bytes / (1024 * 1024)) / max(total_duration, 0.001)
        
        return LoadTestResult(
            total_requests=len(metrics),
            successful_requests=len(successful_metrics),
            failed_requests=len(failed_metrics),
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=len(metrics) / max(total_duration, 0.001),
            total_duration=total_duration,
            error_rate=len(failed_metrics) / len(metrics),
            throughput_mb_per_sec=throughput_mb_per_sec
        )


class SystemResourceMonitor:
    """시스템 리소스 모니터링 클래스"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        
    def start_monitoring(self, interval: float = 1.0):
        """리소스 모니터링 시작"""
        self.monitoring = True
        self.metrics = []
        
        def monitor():
            while self.monitoring:
                try:
                    cpu_percent = psutil.cpu_percent(interval=None)
                    memory = psutil.virtual_memory()
                    disk_io = psutil.disk_io_counters()
                    network_io = psutil.net_io_counters()
                    
                    self.metrics.append({
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_used_mb': memory.used / (1024 * 1024),
                        'memory_available_mb': memory.available / (1024 * 1024),
                        'disk_read_mb': disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
                        'disk_write_mb': disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
                        'network_sent_mb': network_io.bytes_sent / (1024 * 1024) if network_io else 0,
                        'network_recv_mb': network_io.bytes_recv / (1024 * 1024) if network_io else 0,
                    })
                    
                    time.sleep(interval)
                except Exception:
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, any]:
        """리소스 모니터링 중지 및 결과 반환"""
        self.monitoring = False
        
        if not self.metrics:
            return {}
        
        # 통계 계산
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        
        return {
            'duration': self.metrics[-1]['timestamp'] - self.metrics[0]['timestamp'],
            'sample_count': len(self.metrics),
            'cpu': {
                'average': statistics.mean(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average_percent': statistics.mean(memory_values),
                'max_percent': max(memory_values),
                'peak_used_mb': max(m['memory_used_mb'] for m in self.metrics)
            },
            'raw_metrics': self.metrics
        }


def run_performance_test_suite():
    """성능 테스트 스위트 실행"""
    print("⚡ Comix Server 성능 테스트 시작")
    print("=" * 60)
    
    tester = PerformanceTester()
    monitor = SystemResourceMonitor()
    
    # 1. 기본 응답 시간 테스트
    print("\n📊 기본 응답 시간 테스트")
    print("-" * 30)
    
    endpoints = [
        "/",
        "/health",
        "/welcome.102",
        "/manga/"
    ]
    
    for endpoint in endpoints:
        metric = tester.single_request_test(endpoint)
        if metric.error:
            print(f"❌ {endpoint}: 오류 - {metric.error}")
        else:
            print(f"✅ {endpoint}: {metric.response_time:.3f}초 (상태: {metric.status_code})")
    
    # 2. 동시 요청 테스트
    print("\n🔄 동시 요청 테스트")
    print("-" * 30)
    
    monitor.start_monitoring()
    
    concurrent_tests = [
        (10, 5),   # 10개 요청, 5개 동시
        (50, 10),  # 50개 요청, 10개 동시
        (100, 20), # 100개 요청, 20개 동시
    ]
    
    for num_requests, concurrency in concurrent_tests:
        print(f"\n📈 {num_requests}개 요청, {concurrency}개 동시 연결")
        
        result = tester.concurrent_load_test("/", num_requests, concurrency)
        
        print(f"   성공률: {(1 - result.error_rate):.1%}")
        print(f"   평균 응답시간: {result.average_response_time:.3f}초")
        print(f"   95% 응답시간: {result.p95_response_time:.3f}초")
        print(f"   처리량: {result.requests_per_second:.1f} req/sec")
        
        if result.error_rate > 0.1:  # 10% 이상 실패율
            print(f"   ⚠️  높은 실패율: {result.error_rate:.1%}")
    
    # 3. 지속적인 부하 테스트
    print(f"\n⏱️  지속적인 부하 테스트 (30초)")
    print("-" * 30)
    
    sustained_result = tester.sustained_load_test("/", 30, 10)  # 30초간 초당 10요청
    
    print(f"   총 요청: {sustained_result.total_requests}")
    print(f"   성공률: {(1 - sustained_result.error_rate):.1%}")
    print(f"   평균 응답시간: {sustained_result.average_response_time:.3f}초")
    print(f"   실제 처리량: {sustained_result.requests_per_second:.1f} req/sec")
    
    # 4. 시스템 리소스 사용량
    resource_stats = monitor.stop_monitoring()
    
    if resource_stats:
        print(f"\n💻 시스템 리소스 사용량")
        print("-" * 30)
        print(f"   평균 CPU: {resource_stats['cpu']['average']:.1f}%")
        print(f"   최대 CPU: {resource_stats['cpu']['max']:.1f}%")
        print(f"   평균 메모리: {resource_stats['memory']['average_percent']:.1f}%")
        print(f"   최대 메모리: {resource_stats['memory']['peak_used_mb']:.1f}MB")
    
    # 5. 성능 기준 평가
    print(f"\n🎯 성능 기준 평가")
    print("-" * 30)
    
    # 기준값 설정
    criteria = {
        'max_response_time': 1.0,      # 최대 1초
        'min_success_rate': 0.95,      # 최소 95% 성공률
        'min_throughput': 50,          # 최소 50 req/sec
        'max_cpu_usage': 80,           # 최대 80% CPU
        'max_memory_usage': 70         # 최대 70% 메모리
    }
    
    passed_tests = 0
    total_tests = 0
    
    # 응답 시간 평가
    total_tests += 1
    if sustained_result.p95_response_time <= criteria['max_response_time']:
        print(f"✅ 응답 시간: {sustained_result.p95_response_time:.3f}초 ≤ {criteria['max_response_time']}초")
        passed_tests += 1
    else:
        print(f"❌ 응답 시간: {sustained_result.p95_response_time:.3f}초 > {criteria['max_response_time']}초")
    
    # 성공률 평가
    total_tests += 1
    success_rate = 1 - sustained_result.error_rate
    if success_rate >= criteria['min_success_rate']:
        print(f"✅ 성공률: {success_rate:.1%} ≥ {criteria['min_success_rate']:.1%}")
        passed_tests += 1
    else:
        print(f"❌ 성공률: {success_rate:.1%} < {criteria['min_success_rate']:.1%}")
    
    # 처리량 평가
    total_tests += 1
    if sustained_result.requests_per_second >= criteria['min_throughput']:
        print(f"✅ 처리량: {sustained_result.requests_per_second:.1f} req/sec ≥ {criteria['min_throughput']} req/sec")
        passed_tests += 1
    else:
        print(f"❌ 처리량: {sustained_result.requests_per_second:.1f} req/sec < {criteria['min_throughput']} req/sec")
    
    # 리소스 사용량 평가
    if resource_stats:
        total_tests += 2
        
        if resource_stats['cpu']['average'] <= criteria['max_cpu_usage']:
            print(f"✅ CPU 사용량: {resource_stats['cpu']['average']:.1f}% ≤ {criteria['max_cpu_usage']}%")
            passed_tests += 1
        else:
            print(f"❌ CPU 사용량: {resource_stats['cpu']['average']:.1f}% > {criteria['max_cpu_usage']}%")
        
        if resource_stats['memory']['average_percent'] <= criteria['max_memory_usage']:
            print(f"✅ 메모리 사용량: {resource_stats['memory']['average_percent']:.1f}% ≤ {criteria['max_memory_usage']}%")
            passed_tests += 1
        else:
            print(f"❌ 메모리 사용량: {resource_stats['memory']['average_percent']:.1f}% > {criteria['max_memory_usage']}%")
    
    # 최종 결과
    print(f"\n🏆 성능 테스트 결과")
    print("=" * 60)
    print(f"통과한 테스트: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 모든 성능 기준을 만족합니다!")
        return True
    else:
        print("⚠️  일부 성능 기준을 만족하지 못했습니다.")
        print("성능 최적화를 고려해보세요.")
        return False


if __name__ == "__main__":
    try:
        success = run_performance_test_suite()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        exit(1)