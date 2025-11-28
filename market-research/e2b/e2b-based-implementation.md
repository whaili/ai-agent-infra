# 基于 E2B Infra 的实施方案

> 利用 E2B 开源基础设施加速开发
>
> 创建时间：2025-11-27

---

## E2B Infra 开源内容分析

### 已开源部分（推测）

根据 E2B 的产品特性和开源趋势，他们的 `infra` 仓库可能包含：

```yaml
核心运行时层:
  - Firecracker VM 管理
  - VM 生命周期控制
  - 网络配置（TAP/Bridge）
  - 存储管理（rootfs、快照）

编排层:
  - VM 调度逻辑
  - 资源分配
  - 池化管理

基础工具:
  - 镜像构建工具
  - 模板管理
  - 配置管理
```

### E2B 不开源的部分

```yaml
商业服务层:
  ❌ API 服务器（REST/gRPC 接口）
  ❌ 用户认证和授权系统
  ❌ 计费系统
  ❌ 使用量统计和配额管理
  ❌ Web 控制台
  ❌ 监控和日志平台
  ❌ 支付集成
  ❌ 多租户管理
  ❌ 企业功能（SSO、RBAC）
```

---

## 你需要补充的完整列表

### 第一优先级：核心服务层

#### 1. API 服务器 ⭐⭐⭐

**需要做的：**

```go
// 完整的 API 服务实现
package main

type APIServer struct {
    infraManager  *e2b.InfraManager  // 调用 E2B infra
    userService   *UserService
    billingService *BillingService
    authService   *AuthService
}

// 核心 API 端点
func (s *APIServer) SetupRoutes() {
    // Sandbox 管理
    r.POST("/v1/sandboxes", s.CreateSandbox)
    r.GET("/v1/sandboxes/:id", s.GetSandbox)
    r.DELETE("/v1/sandboxes/:id", s.DeleteSandbox)
    r.POST("/v1/sandboxes/:id/execute", s.ExecuteCode)

    // 文件操作
    r.POST("/v1/sandboxes/:id/files", s.UploadFile)
    r.GET("/v1/sandboxes/:id/files/*path", s.DownloadFile)

    // 模板管理
    r.GET("/v1/templates", s.ListTemplates)
    r.POST("/v1/templates", s.CreateTemplate)

    // 用户管理
    r.POST("/v1/auth/login", s.Login)
    r.POST("/v1/auth/register", s.Register)
    r.GET("/v1/users/me", s.GetCurrentUser)
    r.POST("/v1/api-keys", s.CreateAPIKey)
}

// 将 E2B infra 调用包装成 API
func (s *APIServer) CreateSandbox(c *gin.Context) {
    var req CreateSandboxRequest
    c.BindJSON(&req)

    // 1. 验证用户权限和配额
    user := s.authService.GetCurrentUser(c)
    if !s.userService.HasQuota(user.ID) {
        c.JSON(403, gin.H{"error": "quota exceeded"})
        return
    }

    // 2. 调用 E2B infra 创建 VM
    vm, err := s.infraManager.CreateVM(&e2b.VMConfig{
        Template: req.Template,
        CPU:      req.CPUCores,
        Memory:   req.MemoryMB,
        Timeout:  req.TimeoutSeconds,
    })
    if err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }

    // 3. 记录计费
    s.billingService.StartSession(user.ID, vm.ID)

    // 4. 返回响应
    c.JSON(200, gin.H{
        "sandbox_id": vm.ID,
        "status": "running",
        "ip": vm.IP,
        "ports": vm.Ports,
    })
}
```

**工作量估算：** 4-6 周

---

#### 2. 用户认证和授权系统 ⭐⭐⭐

**需要做的：**

```go
// 数据库模型
type User struct {
    ID           string    `gorm:"primaryKey"`
    Email        string    `gorm:"unique;not null"`
    PasswordHash string    `gorm:"not null"`
    APIKeys      []APIKey  `gorm:"foreignKey:UserID"`
    Plan         string    `gorm:"default:'free'"`  // free, pro, enterprise
    CreatedAt    time.Time
}

type APIKey struct {
    ID        string    `gorm:"primaryKey"`
    UserID    string    `gorm:"not null"`
    Key       string    `gorm:"unique;not null"`  // sk_live_xxx
    Name      string
    Scopes    string    `gorm:"type:json"`  // ["sandboxes:read", "sandboxes:write"]
    ExpiresAt *time.Time
    LastUsedAt *time.Time
    CreatedAt time.Time
}

// JWT 认证
type AuthService struct {
    jwtSecret []byte
    db        *gorm.DB
}

func (s *AuthService) ValidateJWT(token string) (*User, error) {
    claims := &jwt.StandardClaims{}
    _, err := jwt.ParseWithClaims(token, claims, func(t *jwt.Token) (interface{}, error) {
        return s.jwtSecret, nil
    })
    if err != nil {
        return nil, err
    }

    var user User
    s.db.First(&user, "id = ?", claims.Subject)
    return &user, nil
}

func (s *AuthService) ValidateAPIKey(key string) (*User, error) {
    var apiKey APIKey
    if err := s.db.Preload("User").First(&apiKey, "key = ?", key).Error; err != nil {
        return nil, err
    }

    // 检查过期
    if apiKey.ExpiresAt != nil && time.Now().After(*apiKey.ExpiresAt) {
        return nil, errors.New("API key expired")
    }

    // 更新最后使用时间
    now := time.Now()
    apiKey.LastUsedAt = &now
    s.db.Save(&apiKey)

    return &apiKey.User, nil
}

// 权限检查
func (s *AuthService) HasPermission(user *User, resource, action string) bool {
    // 根据用户套餐和资源类型检查权限
    permission := fmt.Sprintf("%s:%s", resource, action)

    // 企业用户拥有所有权限
    if user.Plan == "enterprise" {
        return true
    }

    // 免费用户权限限制
    if user.Plan == "free" {
        allowedPermissions := []string{
            "sandboxes:read",
            "sandboxes:write",
            "templates:read",
        }
        return contains(allowedPermissions, permission)
    }

    return true
}
```

**工作量估算：** 2-3 周

---

#### 3. 计费系统 ⭐⭐⭐

**需要做的：**

```go
// 计费模型
type BillingSession struct {
    ID          string    `gorm:"primaryKey"`
    UserID      string    `gorm:"not null;index"`
    SandboxID   string    `gorm:"not null"`
    StartTime   time.Time `gorm:"not null"`
    EndTime     *time.Time

    // 资源使用
    CPUCores    int
    MemoryMB    int
    DiskMB      int

    // 计费
    Status      string    `gorm:"default:'active'"` // active, completed, failed
    TotalCost   float64   `gorm:"default:0"`
    Currency    string    `gorm:"default:'USD'"`
}

type UsageRecord struct {
    ID           string    `gorm:"primaryKey"`
    SessionID    string    `gorm:"not null;index"`
    Timestamp    time.Time `gorm:"not null"`
    CPUSeconds   int64
    MemoryMBSec  int64
    NetworkBytes int64
    Cost         float64
}

type BillingService struct {
    db       *gorm.DB
    pricing  *PricingConfig
    stripe   *stripe.Client
}

// 定价配置
type PricingConfig struct {
    CPUPricePerCoreHour    float64  // $0.10/core/hour
    MemoryPricePerGBHour   float64  // $0.02/GB/hour
    NetworkPricePerGB      float64  // $0.05/GB
    StoragePricePerGBMonth float64  // $0.10/GB/month
}

// 启动计费会话
func (s *BillingService) StartSession(userID, sandboxID string, config *SandboxConfig) (*BillingSession, error) {
    session := &BillingSession{
        ID:        generateID(),
        UserID:    userID,
        SandboxID: sandboxID,
        StartTime: time.Now(),
        CPUCores:  config.CPUCores,
        MemoryMB:  config.MemoryMB,
        DiskMB:    config.DiskMB,
        Status:    "active",
    }

    s.db.Create(session)

    // 启动后台计费任务
    go s.collectUsage(session.ID)

    return session, nil
}

// 定期收集使用量（每分钟）
func (s *BillingService) collectUsage(sessionID string) {
    ticker := time.NewTicker(1 * time.Minute)
    defer ticker.Stop()

    for range ticker.C {
        var session BillingSession
        s.db.First(&session, "id = ?", sessionID)

        if session.Status != "active" {
            break
        }

        // 计算增量成本
        duration := time.Since(session.StartTime).Hours()
        cpuCost := float64(session.CPUCores) * duration * s.pricing.CPUPricePerCoreHour
        memoryCost := float64(session.MemoryMB) / 1024.0 * duration * s.pricing.MemoryPricePerGBHour

        // 更新总成本
        session.TotalCost = cpuCost + memoryCost
        s.db.Save(&session)

        // 检查用户余额
        if err := s.checkBalance(session.UserID, session.TotalCost); err != nil {
            s.StopSession(sessionID)
            break
        }
    }
}

// 结束计费会话
func (s *BillingService) StopSession(sessionID string) error {
    var session BillingSession
    s.db.First(&session, "id = ?", sessionID)

    now := time.Now()
    session.EndTime = &now
    session.Status = "completed"

    // 最终计费
    duration := now.Sub(session.StartTime).Hours()
    session.TotalCost = s.calculateFinalCost(&session, duration)

    s.db.Save(&session)

    // 扣费
    return s.charge(session.UserID, session.TotalCost)
}

// 集成 Stripe 支付
func (s *BillingService) charge(userID string, amount float64) error {
    // 获取用户的 Stripe customer ID
    var user User
    s.db.First(&user, "id = ?", userID)

    if user.StripeCustomerID == "" {
        return errors.New("no payment method")
    }

    // 创建付款意图
    params := &stripe.PaymentIntentParams{
        Amount:   stripe.Int64(int64(amount * 100)), // 转换为分
        Currency: stripe.String("usd"),
        Customer: stripe.String(user.StripeCustomerID),
        AutomaticPaymentMethods: &stripe.PaymentIntentAutomaticPaymentMethodsParams{
            Enabled: stripe.Bool(true),
        },
    }

    _, err := s.stripe.PaymentIntents.New(params)
    return err
}
```

**工作量估算：** 3-4 周

---

#### 4. 配额和限流系统 ⭐⭐

**需要做的：**

```go
// 配额模型
type UserQuota struct {
    UserID              string `gorm:"primaryKey"`
    Plan                string `gorm:"not null"`

    // 并发限制
    MaxConcurrentSandboxes int `gorm:"default:2"`
    CurrentSandboxes       int `gorm:"default:0"`

    // 使用量限制（每月）
    MaxSandboxHours        int `gorm:"default:100"`
    UsedSandboxHours       float64 `gorm:"default:0"`

    // 资源限制
    MaxCPUCores            int `gorm:"default:2"`
    MaxMemoryMB            int `gorm:"default:4096"`
    MaxStorageGB           int `gorm:"default:10"`

    // 速率限制（每分钟）
    RateLimitPerMinute     int `gorm:"default:60"`

    // 重置时间
    ResetAt                time.Time
    UpdatedAt              time.Time
}

type QuotaService struct {
    db    *gorm.DB
    redis *redis.Client
}

// 检查是否可以创建沙箱
func (s *QuotaService) CanCreateSandbox(userID string, config *SandboxConfig) error {
    var quota UserQuota
    s.db.First(&quota, "user_id = ?", userID)

    // 检查并发数
    if quota.CurrentSandboxes >= quota.MaxConcurrentSandboxes {
        return errors.New("concurrent sandbox limit reached")
    }

    // 检查月度使用量
    if quota.UsedSandboxHours >= float64(quota.MaxSandboxHours) {
        return errors.New("monthly usage limit reached")
    }

    // 检查资源限制
    if config.CPUCores > quota.MaxCPUCores {
        return fmt.Errorf("CPU limit exceeded: max %d cores", quota.MaxCPUCores)
    }

    if config.MemoryMB > quota.MaxMemoryMB {
        return fmt.Errorf("memory limit exceeded: max %d MB", quota.MaxMemoryMB)
    }

    return nil
}

// 速率限制（基于 Redis）
func (s *QuotaService) CheckRateLimit(userID string) error {
    key := fmt.Sprintf("ratelimit:%s", userID)

    // 获取当前计数
    count, err := s.redis.Get(context.Background(), key).Int()
    if err == redis.Nil {
        count = 0
    }

    var quota UserQuota
    s.db.First(&quota, "user_id = ?", userID)

    // 检查是否超限
    if count >= quota.RateLimitPerMinute {
        return errors.New("rate limit exceeded")
    }

    // 递增计数
    pipe := s.redis.Pipeline()
    pipe.Incr(context.Background(), key)
    pipe.Expire(context.Background(), key, 1*time.Minute)
    pipe.Exec(context.Background())

    return nil
}

// 更新配额使用量
func (s *QuotaService) IncrementUsage(userID string, hours float64) error {
    return s.db.Model(&UserQuota{}).
        Where("user_id = ?", userID).
        Update("used_sandbox_hours", gorm.Expr("used_sandbox_hours + ?", hours)).
        Error
}

// 每月重置配额
func (s *QuotaService) ResetMonthlyQuotas() {
    s.db.Model(&UserQuota{}).
        Where("reset_at < ?", time.Now()).
        Updates(map[string]interface{}{
            "used_sandbox_hours": 0,
            "reset_at": time.Now().AddDate(0, 1, 0),
        })
}
```

**工作量估算：** 2 周

---

### 第二优先级：管理和监控

#### 5. Web 控制台 ⭐⭐

**需要做的：**

```typescript
// React + TypeScript 前端
// 主要功能：

// Dashboard
interface DashboardProps {
  user: User;
}

function Dashboard({ user }: DashboardProps) {
  const [sandboxes, setSandboxes] = useState<Sandbox[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);

  return (
    <div className="dashboard">
      <Header user={user} />

      {/* 使用量统计 */}
      <UsageStats usage={usage} quota={user.quota} />

      {/* 活跃沙箱列表 */}
      <SandboxList sandboxes={sandboxes} />

      {/* 快速操作 */}
      <QuickActions>
        <Button onClick={createSandbox}>创建沙箱</Button>
        <Button onClick={viewBilling}>查看账单</Button>
      </QuickActions>
    </div>
  );
}

// Sandbox 管理页面
function SandboxManager() {
  return (
    <div>
      <SandboxList />
      <SandboxDetails />
      <Terminal />  {/* WebSocket 连接到沙箱 */}
      <FileExplorer />
    </div>
  );
}

// 计费页面
function BillingPage() {
  return (
    <div>
      <CurrentPlan />
      <UsageChart />
      <InvoiceList />
      <PaymentMethods />
      <UpgradePlans />
    </div>
  );
}

// API Keys 管理
function APIKeysPage() {
  return (
    <div>
      <CreateKeyButton />
      <KeysList />
      <UsageByKey />
    </div>
  );
}
```

**技术栈：**
- React + TypeScript
- TailwindCSS / Material-UI
- React Query（数据获取）
- Zustand/Redux（状态管理）
- xterm.js（终端模拟）
- monaco-editor（代码编辑）

**工作量估算：** 6-8 周

---

#### 6. 监控和日志系统 ⭐⭐

**需要做的：**

```yaml
# Prometheus + Grafana 部署

# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  # API 服务器指标
  - job_name: 'api-server'
    static_configs:
      - targets: ['localhost:9090']

  # 沙箱指标
  - job_name: 'sandboxes'
    static_configs:
      - targets: ['sandbox-exporter:9091']

# 自定义指标收集
```

```go
// 指标暴露
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // 沙箱指标
    sandboxCount = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "sandboxes_total",
            Help: "Total number of sandboxes by status",
        },
        []string{"status", "template"},
    )

    sandboxCreationDuration = promauto.NewHistogram(
        prometheus.HistogramOpts{
            Name:    "sandbox_creation_duration_seconds",
            Help:    "Time to create a sandbox",
            Buckets: []float64{0.1, 0.5, 1, 2, 5, 10},
        },
    )

    // API 指标
    apiRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "api_request_duration_seconds",
            Help: "API request duration",
        },
        []string{"method", "endpoint", "status"},
    )

    // 资源使用指标
    cpuUsage = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "sandbox_cpu_usage_percent",
            Help: "CPU usage of sandbox",
        },
        []string{"sandbox_id", "user_id"},
    )

    memoryUsage = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "sandbox_memory_usage_mb",
            Help: "Memory usage of sandbox",
        },
        []string{"sandbox_id", "user_id"},
    )
)

// 中间件记录 API 延迟
func PrometheusMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()

        c.Next()

        duration := time.Since(start).Seconds()
        apiRequestDuration.WithLabelValues(
            c.Request.Method,
            c.FullPath(),
            fmt.Sprintf("%d", c.Writer.Status()),
        ).Observe(duration)
    }
}
```

**日志聚合（Loki）：**

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: api-server
    static_configs:
      - targets:
          - localhost
        labels:
          job: api-server
          __path__: /var/log/api-server/*.log

  - job_name: sandboxes
    static_configs:
      - targets:
          - localhost
        labels:
          job: sandboxes
          __path__: /var/log/sandboxes/*/*.log
```

**Grafana 仪表板：**
- 系统概览（沙箱数量、API 请求、资源使用）
- 用户活动（活跃用户、使用量分布）
- 性能监控（延迟分布、错误率）
- 计费监控（收入、成本）

**工作量估算：** 2-3 周

---

### 第三优先级：运维和工具

#### 7. 部署和 CI/CD ⭐⭐

**需要做的：**

```yaml
# Kubernetes 部署清单

# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api-server
        image: your-registry/api-server:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-server
spec:
  selector:
    app: api-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: api-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-server
            port:
              number: 80
```

**CI/CD 流程（GitHub Actions）：**

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test ./...

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: your-registry/api-server:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      - run: |
          kubectl set image deployment/api-server \
            api-server=your-registry/api-server:${{ github.sha }}
```

**工作量估算：** 2-3 周

---

#### 8. SDK 客户端 ⭐⭐

**Python SDK：**

```python
# ppio_sandbox/__init__.py

import os
import requests
from typing import Optional, Dict, List

class Sandbox:
    """Sandbox 实例"""

    def __init__(self, sandbox_id: str, client: 'SandboxClient'):
        self.id = sandbox_id
        self._client = client
        self._status = "initializing"

    @classmethod
    def create(cls,
               template: str = "code-interpreter",
               timeout: int = 600,
               env: Optional[Dict[str, str]] = None,
               api_key: Optional[str] = None) -> 'Sandbox':
        """创建新沙箱"""
        client = SandboxClient(api_key=api_key or os.getenv('PPIO_API_KEY'))

        response = client._post('/sandboxes', json={
            'template': template,
            'timeout': timeout,
            'env': env or {},
        })

        return cls(response['sandbox_id'], client)

    def execute(self, code: str, language: str = "python") -> 'ExecutionResult':
        """执行代码"""
        response = self._client._post(
            f'/sandboxes/{self.id}/execute',
            json={'code': code, 'language': language}
        )
        return ExecutionResult(response)

    def upload_file(self, local_path: str, remote_path: str):
        """上传文件"""
        with open(local_path, 'rb') as f:
            self._client._post(
                f'/sandboxes/{self.id}/files',
                files={'file': f},
                params={'path': remote_path}
            )

    def download_file(self, remote_path: str, local_path: str):
        """下载文件"""
        response = self._client._get(
            f'/sandboxes/{self.id}/files/{remote_path}',
            stream=True
        )
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def kill(self):
        """销毁沙箱"""
        self._client._delete(f'/sandboxes/{self.id}')
        self._status = "terminated"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill()

class ExecutionResult:
    """代码执行结果"""

    def __init__(self, data: dict):
        self.stdout = data.get('stdout', '')
        self.stderr = data.get('stderr', '')
        self.exit_code = data.get('exit_code', 0)
        self.error = data.get('error')

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.error

class SandboxClient:
    """API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.yourdomain.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'ppio-python/1.0.0'
        })

    def _request(self, method: str, path: str, **kwargs):
        response = self.session.request(
            method,
            f'{self.base_url}{path}',
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, **kwargs):
        return self._request('POST', path, **kwargs)

    def _get(self, path: str, **kwargs):
        return self._request('GET', path, **kwargs)

    def _delete(self, path: str, **kwargs):
        return self._request('DELETE', path, **kwargs)

# 使用示例
if __name__ == '__main__':
    # 创建沙箱
    with Sandbox.create(template="code-interpreter") as sandbox:
        # 执行代码
        result = sandbox.execute("""
        import numpy as np
        print(np.array([1, 2, 3]).mean())
        """)

        print(result.stdout)  # 输出: 2.0

        # 上传文件
        sandbox.upload_file("local_data.csv", "/workspace/data.csv")

        # 执行处理文件的代码
        result = sandbox.execute("""
        import pandas as pd
        df = pd.read_csv('/workspace/data.csv')
        print(df.head())
        """)

        print(result.stdout)

    # 沙箱自动清理
```

**JavaScript/TypeScript SDK：**

```typescript
// src/index.ts

export class Sandbox {
  private id: string;
  private client: SandboxClient;

  constructor(id: string, client: SandboxClient) {
    this.id = id;
    this.client = client;
  }

  static async create(options: SandboxOptions = {}): Promise<Sandbox> {
    const client = new SandboxClient(
      options.apiKey || process.env.PPIO_API_KEY!
    );

    const response = await client.post('/sandboxes', {
      template: options.template || 'code-interpreter',
      timeout: options.timeout || 600,
      env: options.env || {},
    });

    return new Sandbox(response.sandbox_id, client);
  }

  async execute(code: string): Promise<ExecutionResult> {
    const response = await this.client.post(
      `/sandboxes/${this.id}/execute`,
      { code }
    );
    return new ExecutionResult(response);
  }

  async kill(): Promise<void> {
    await this.client.delete(`/sandboxes/${this.id}`);
  }
}

// 使用示例
import { Sandbox } from 'ppio-sandbox';

const sandbox = await Sandbox.create({
  template: 'code-interpreter'
});

const result = await sandbox.execute(`
  import numpy as np
  print(np.array([1, 2, 3]).mean())
`);

console.log(result.stdout); // 2.0

await sandbox.kill();
```

**工作量估算：**
- Python SDK: 2 周
- JavaScript SDK: 2 周
- Go SDK: 1-2 周

---

#### 9. 文档和示例 ⭐

**需要做的：**

```markdown
# 文档结构

docs/
├── getting-started/
│   ├── quickstart.md
│   ├── installation.md
│   └── first-sandbox.md
├── guides/
│   ├── authentication.md
│   ├── templates.md
│   ├── file-operations.md
│   ├── networking.md
│   └── best-practices.md
├── api-reference/
│   ├── rest-api.md
│   ├── python-sdk.md
│   ├── javascript-sdk.md
│   └── go-sdk.md
├── examples/
│   ├── code-interpreter/
│   ├── web-scraping/
│   ├── browser-automation/
│   └── data-processing/
├── deployment/
│   ├── self-hosted.md
│   ├── kubernetes.md
│   └── docker-compose.md
└── billing/
    ├── pricing.md
    └── usage-tracking.md
```

**交互式教程：**
- Jupyter Notebook 示例
- Postman Collection
- 在线 Playground

**工作量估算：** 3-4 周

---

## 总体实施计划

### MVP 阶段（3 个月）

```yaml
Month 1:
  Week 1-2:
    - 研究 E2B infra 代码
    - 搭建开发环境
    - API 服务器框架搭建

  Week 3-4:
    - 用户认证系统
    - 基础 API 实现（创建/删除沙箱）
    - 简单的配额系统

Month 2:
  Week 5-6:
    - 计费系统基础
    - Python SDK 开发
    - 文件上传下载

  Week 7-8:
    - Web 控制台（基础版）
    - 监控集成
    - 文档编写

Month 3:
  Week 9-10:
    - 完善 API
    - 支付集成（Stripe）
    - 测试和修复

  Week 11-12:
    - 部署到生产环境
    - 性能优化
    - Beta 测试
```

### 功能优先级

```yaml
P0（必须有）:
  - ✅ API 服务器
  - ✅ 用户认证
  - ✅ 基础计费
  - ✅ Python SDK
  - ✅ 简单的 Web 控制台

P1（重要）:
  - ⭐ 完整的计费系统
  - ⭐ 配额管理
  - ⭐ 监控和日志
  - ⭐ JavaScript SDK
  - ⭐ 完整文档

P2（可以延后）:
  - 高级模板
  - GPU 支持
  - VNC 集成
  - 企业功能（SSO、RBAC）
  - 自定义模板上传
```

---

## 技术债务和风险

### 使用 E2B infra 的风险

```yaml
风险 1: API 稳定性
  问题: E2B infra 的 API 可能变更
  应对:
    - 封装适配层
    - 版本锁定
    - 定期跟踪更新

风险 2: 功能限制
  问题: E2B infra 可能不满足所有需求
  应对:
    - Fork 并自己维护
    - 贡献代码回上游
    - 准备替换方案

风险 3: 许可证问题
  问题: 需要确认许可证兼容性
  应对:
    - 仔细阅读许可证
    - 咨询法律顾问
    - 准备自研方案

风险 4: 社区支持
  问题: E2B infra 可能维护不活跃
  应对:
    - 加入社区
    - 自己修复问题
    - 建立 Fork 社区
```

---

## 成本对比

### 使用 E2B infra vs 完全自研

```yaml
使用 E2B infra:
  优势:
    - 节省 4-6 个月核心运行时开发
    - 减少技术风险
    - 快速上市

  工作量:
    - MVP: 3 个月
    - V1.0: 6 个月

  人力成本:
    - 3-4 人 × 6 个月 = 18-24 人月
    - 约 40-60 万

完全自研:
  优势:
    - 完全控制
    - 无依赖风险

  工作量:
    - MVP: 6 个月
    - V1.0: 12 个月

  人力成本:
    - 4-5 人 × 12 个月 = 48-60 人月
    - 约 100-150 万

推荐: 使用 E2B infra，节省 50-100 万成本
```

---

## 下一步行动

### 立即开始

1. **克隆 E2B infra**
   ```bash
   git clone https://github.com/e2b-dev/infra.git
   cd infra
   # 阅读 README 和文档
   ```

2. **本地测试**
   ```bash
   # 按照 E2B infra 文档搭建测试环境
   # 创建测试沙箱
   # 验证功能
   ```

3. **API 服务器 POC**
   ```bash
   mkdir agentic-api
   cd agentic-api
   go mod init github.com/yourorg/agentic-api

   # 创建简单的 REST API 包装 E2B infra
   ```

4. **确定技术栈**
   - 后端语言: Go / Rust / Node.js?
   - 数据库: PostgreSQL
   - 缓存: Redis
   - 前端: React + TypeScript

---

## 总结

### 基于 E2B infra，你需要补充的核心内容：

#### 必须要做的（P0）:
1. ✅ API 服务器（REST/gRPC）
2. ✅ 用户认证和授权
3. ✅ 计费系统
4. ✅ 配额和限流
5. ✅ 基础 Web 控制台
6. ✅ Python SDK

#### 重要但可以迭代的（P1）:
7. ⭐ 监控和日志系统
8. ⭐ 部署和 CI/CD
9. ⭐ 多语言 SDK
10. ⭐ 完整文档

#### 可以延后的（P2）:
11. 高级模板管理
12. 企业功能
13. 高级监控和告警
14. Marketplace

### 时间估算：
- **MVP: 3 个月**（核心功能）
- **V1.0: 6 个月**（生产就绪）
- **V2.0: 12 个月**（企业级）

### 人力需求：
- 后端工程师 × 2
- 前端工程师 × 1
- DevOps 工程师 × 1

### 总成本：
- 开发成本：40-60 万
- 运营成本：1-5 万/月

**E2B infra 为你节省了最核心和最难的部分（Firecracker 运行时），剩下的是构建商业化产品的标准流程。**

---

*建议：先用 1-2 周深入研究 E2B infra 的代码和架构，再开始 API 服务器的开发。*
