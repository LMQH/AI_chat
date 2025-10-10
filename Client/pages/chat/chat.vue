<template>
	<view class="container" @touchstart="touchStart" @touchmove="touchMove" @touchend="touchEnd">

		<!-- 聊天页面 -->
		<view class="chat-page" :style="{ transform: 'translateX(' + offsetX + 'px)', 
				        backgroundColor: 'rgba(230,230,230,' + navOpacity + ')' }">

			<!-- 导航栏 -->
			<view class="nav-bar" :style="{ 
				        paddingTop: statusBarHeight + 'px'}">

				<view class="nav-content" :class="{ 'nav-dim': showSidebar }">
					<!-- 左侧图标按钮 -->
					<view class="nav-btn">
						<image @click="openSidebar" src="/static/icons/chat-line-round.png" mode="aspectFit"
							class="icon">
						</image>
					</view>

					<!-- 中间标题和身份选择 -->
					<view class="nav-title-container">
						<view class="nav-title">AI</view>
						<view class="identity-selector" @click="showIdentitySelector = !showIdentitySelector">
							<text class="identity-name">{{ currentIdentityName }}</text>
							<image src="/static/icons/arrow-down.png" mode="aspectFit" class="arrow-icon"></image>
						</view>
					</view>

					<!-- 右侧图标按钮 -->
					<view class="nav-btn">
						<image @click="MessagesPlus" src="/static/icons/message_plus.png" mode="aspectFit" class="icon">
						</image>
					</view>
				</view>
			</view>

			<!-- 身份选择下拉菜单 -->
			<view class="identity-dropdown" v-if="showIdentitySelector" @click.stop>
				<view class="identity-list">
					<view v-for="identity in availableIdentities" :key="identity.id" 
						class="identity-item" 
						:class="{ 'active': identity.id === currentIdentityId }"
						@click="selectIdentity(identity.id)">
						<view class="identity-info">
							<text class="identity-item-name">{{ identity.name }}</text>
							<text class="identity-item-desc">{{ identity.description }}</text>
						</view>
						<view v-if="identity.id === currentIdentityId" class="check-icon">
							<image src="/static/icons/check.png" mode="aspectFit"></image>
						</view>
					</view>
				</view>
			</view>

			<!-- 底部输入框 -->
			<view class="input-bar">
				<input class="input" v-model="inputValue" placeholder="输入消息..." />
				<view class="upload-btn" :class="{ 'uploaded': hasAttachment }" @click="pickAndUpload">
					<image src="/static/icons/upload.png" mode="aspectFit" class="upload-icon"></image>
				</view>
				<button class="send-btn" @click="sendMessage">发送</button>
			</view>

			<!-- 对话消息 -->
			<scroll-view class="chat-container" scroll-y :scroll-with-animation="true" enable-back-to-top
				:scroll-into-view="scrollToViewId"
				:style="{
					height: scrollViewHeight + 'px',
					paddingTop: (statusBarHeight + navContentHeight + extraTopGap) + 'px',
					paddingBottom: (inputBarHeight + extraBottomGap) + 'px'
				}">
				<view v-for="(item, index) in arr" :key="index" :id="'msg-' + index"
					:class="['chat-item', item.flag <= 3 ? 'ai' : 'user']">
					<image class="avatar" :src="item.touxiang" mode="aspectFit"></image>
					<view class="content">
						<!-- 文本 -->
						<view v-if="item.flag === 1 || item.flag === 4" class="text-msg">
							<view v-if="item.flag === 1" v-html="renderMarkdown(item.text)" class="markdown-content"></view>
							<view v-else>{{ item.text }}</view>
						</view>
						<!-- 附件预览：图片或链接 -->
						<view v-if="item.isAttachment && item.attachUrl" class="attach-block">
							<image v-if="/\.(png|jpe?g|webp|gif)$/i.test(item.attachUrl)" :src="item.attachUrl" class="img-thumb" @click="openLink(item.attachUrl)"></image>
							<view v-else class="link-msg" @click="openLink(item.attachUrl)">{{ item.attachUrl }}</view>
						</view>
						<!-- 图片 -->
						<image v-else-if="item.flag === 2 || item.flag === 5" :src="item.img" class="img-thumb" @click="openLink(item.img)">
						</image>
						<!-- 视频 -->
						<video v-else-if="item.flag === 3 || item.flag === 6" :src="item.v" class="video-msg"
							controls></video>
					</view>
				</view>
			</scroll-view>
		</view>


		<!-- 半透明蒙层 -->
		<view class="overlay" v-if="offsetX>0"
			:style="{ backgroundColor: 'rgba(0,0,0,' + (0.4 * offsetX/maxOffset) + ')' }" @click="hideSidebar">
		</view>

		<!-- 左侧菜单 -->
		<view class="sidebar" :style="{ left: (-70* (1 - offsetX/maxOffset)) + '%' }">
		    <view class="sidebar-header">对话主题</view>
			<scroll-view scroll-y class="sidebar-list">
		        <view v-if="subjectsLoading" class="sidebar-item">加载中...</view>
		        <view v-else-if="subjects.length === 0" class="sidebar-item">暂无对话</view>
		        <view v-else v-for="item in subjects" :key="'subject-'+item.id" class="sidebar-item" @click="openSubject(item.id)" :class="{ 'active': item.id === currentSubjectId, 'swiping': (subjectSwipeX[item.id]||0) < -20 }"
		            @touchstart.stop="subjectTouchStart($event, item.id)"
		            @touchmove.stop="subjectTouchMove($event, item.id)"
		            @touchend.stop="subjectTouchEnd($event, item.id)"
		        >
		            <view class="subject-swipe" :style="{ transform: 'translateX(' + (subjectSwipeX[item.id]||0) + 'px)' }">
		                <text class="subject-title">{{ item.title }}</text>
		            </view>
		            <view class="subject-delete" @click.stop="confirmDeleteSubject(item.id)">
		                <image src="/static/icons/delete.png" mode="aspectFit" class="delete-icon"></image>
		            </view>
				</view>
			</scroll-view>
			
			<!-- 侧边栏右下角刷新按钮 -->
			<view class="sidebar-refresh-btn" :class="{ rotating: isRefreshing }" @click="refreshVectorDB">
				<image src="/static/icons/shuaxin.png" mode="aspectFit"></image>
			</view>
		</view>

		<!-- 自定义Toast弹窗 -->
		<view v-if="showCustomToast" class="custom-toast">
			<view class="toast-content" :class="toastType">
				<text class="toast-text">{{ toastMessage }}</text>
			</view>
		</view>

		<!-- 预览弹窗 -->
		<view v-if="previewVisible" class="preview-mask" @click="closePreview">
			<view class="preview-dialog" @click.stop>
				<view class="preview-header">
					<text class="preview-title">附件预览</text>
					<view class="preview-close" @click="closePreview">×</view>
				</view>
				<view class="preview-body">
					<image v-if="/\.(png|jpe?g|webp|gif)$/i.test(previewUrl)" :src="previewUrl" mode="widthFix" class="preview-image"></image>
					<view v-else class="preview-link" @click="openLink(previewUrl)">{{ previewUrl }}</view>
				</view>
			</view>
		</view>

	</view>>
</template>

<script>
	export default {
		data() {
			return {
				showSidebar: false,
				statusBarHeight: 0,
				startX: 0,
				endX: 0,
				offsetX: 0,
				touching: false,

				maxOffset: 250, // 左侧抽屉宽度

				inputValue: '', // 初始化输入框
				messages: [],
				subjects: [],
				subjectsLoading: false,
				
				// 身份选择相关
				showIdentitySelector: false,
				availableIdentities: [],
				currentIdentityId: 'default',
				currentIdentityName: '通用AI助手',
				// 侧边栏主题滑动删除交互
				subjectSwipeX: {},
				subjectTouchStartX: 0,
				deleteWidth: 60, // 删除按钮宽度（px）
				arr: [{
					flag: 1, // AI文本消息
					touxiang: "/static/touxiang/agent.png", // 假设这是AI头像
					text: "欢迎使用AI系统"
				}],
				// 后端基础地址（按需修改端口）
				backendBase: 'http://localhost:8000',
				// 当前会话主题ID，0 表示新建
				currentSubjectId: 0,
				// 流控制
				isStreaming: false,
				abortController: null,
				// 附件上传
				hasAttachment: false,
				attachmentUrl: '',
				// 预览弹窗
				previewVisible: false,
				previewUrl: '',
				// 固定高度常量（rpx转px需乘以2，因uni-app默认rpx基于750宽屏）
				navContentHeight: 44, // nav-content高度88rpx = 44px（750屏1rpx=0.5px）
				inputBarHeight: 56, // input-bar总高度：82rpx(input) + 30rpx(padding) = 112rpx = 56px
				scrollViewHeight: 0, // 聊天滚动容器高度（px）
				extraTopGap: 12, // 顶部额外留白（px）
				extraBottomGap: 12, // 底部额外留白（px）
				scrollToViewId: '', // 滚动锚点ID，用于scroll-view原生滚动
				// 向量数据库刷新
				isRefreshing: false, // 是否正在刷新向量数据库
				// 自定义提示弹窗
				showCustomToast: false,
				toastMessage: '',
				toastType: 'success' // success, error
			}
		},
		onLoad() {
			// 获取状态栏高度，保证导航栏沉浸式
			uni.getSystemInfo({
				success: (res) => {
					this.statusBarHeight = res.statusBarHeight
					// 注入 CSS 变量，方便使用
					if (typeof document !== 'undefined') {
						document.documentElement.style.setProperty(
							'--status-bar-height', res.statusBarHeight + 'px');
					}
					// 计算滚动区域的像素高度（windowHeight - 顶部导航 - 底部输入条）
					const topH = this.statusBarHeight + this.navContentHeight;
					this.scrollViewHeight = Math.max(0, Math.floor(res.windowHeight - topH - this.inputBarHeight));
				}
			})
		},
		onShow() {
			this.fetchSubjects();
		},
		computed: {
			navOpacity() {
				return 1 - this.offsetX / this.maxOffset * 0.5; // 最大半透明灰度
			}
		},
		methods: {
			// 刷新向量数据库
			async refreshVectorDB() {
				if (this.isRefreshing) {
					return; // 防止重复点击
				}
				
				this.isRefreshing = true;
				
				try {
					// 调用后端API智能刷新向量数据库
					const response = await uni.request({
						url: `${this.backendBase}/refresh_vector_db`,
						method: 'POST',
						timeout: 300000 // 超时时间，因为重建可能需要较长时间
					});
					
					if (response.data && response.data.success) {
						// 根据操作类型显示不同的成功消息
						const action = response.data.action;
						let title = '知识库刷新成功';
						
						if (action === 'reload') {
							title = '知识库已重新加载';
						} else if (action === 'rebuild') {
							title = '知识库已重建完成';
						} else if (action === 'update') {
							title = '知识库已更新完成';
						}
						
						// 使用自定义Toast，显示处理时间
						const elapsedTime = response.data.elapsed_time || 0;
						const timeText = elapsedTime > 0 ? ` (耗时: ${elapsedTime}秒)` : '';
						
						this.showCustomToast = true;
						this.toastMessage = title + timeText;
						this.toastType = 'success';
						
						// 3秒后自动关闭
						setTimeout(() => {
							this.showCustomToast = false;
						}, 3000);
					} else {
						throw new Error(response.data?.message || '刷新失败');
					}
					
				} catch (error) {
					console.error('刷新向量数据库失败:', error);
					
					// 使用自定义Toast显示错误
					this.showCustomToast = true;
					this.toastMessage = '刷新失败: ' + (error.message || '未知错误');
					this.toastType = 'error';
					
					// 4秒后自动关闭
					setTimeout(() => {
						this.showCustomToast = false;
					}, 4000);
				} finally {
					// RAG重建完成后停止旋转
					this.isRefreshing = false;
				}
			},
			
			// Markdown 渲染方法
			renderMarkdown(text) {
				if (!text) return '';
				
				
				// 转义 HTML 特殊字符
				const escapeHtml = (str) => {
					return str
						.replace(/&/g, '&amp;')
						.replace(/</g, '&lt;')
						.replace(/>/g, '&gt;')
						.replace(/"/g, '&quot;')
						.replace(/'/g, '&#39;');
				};
				
				// 处理 Markdown 语法
				let html = text;
				
				// 先处理代码块，避免内部内容被其他规则影响
				html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
					return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
				});
				
				// 处理行内代码
				html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');
				
				// 进行HTML转义，确保安全性
				html = escapeHtml(html);
				
				// 处理转义后的思考标签：将 &lt;think&gt;和 &lt;/think&gt;替换为思考块
				html = html.replace(/&lt;think&gt;([\s\S]*?)&lt;\/think&gt;/gi, (match, content) => {
					return `<div class="thinking-block" style="background-color: #ffffff; color: #999999; border: 2px solid #666666; padding: 20rpx; border-radius: 12rpx; margin: 16rpx 0; font-style: italic; font-weight: 600;">${content.trim()}</div>`;
				});
				
				// 恢复代码块（避免被转义）
				html = html.replace(/&lt;pre&gt;&lt;code&gt;(.*?)&lt;\/code&gt;&lt;\/pre&gt;/g, '<pre><code>$1</code></pre>');
				html = html.replace(/&lt;code&gt;(.*?)&lt;\/code&gt;/g, '<code>$1</code>');
				
				// 标题
				html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
				html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
				html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
				
				// 粗体和斜体
				html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
				html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
				
				// 链接
				html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
				
				// 列表处理
				const lines = html.split('\n');
				let inList = false;
				let result = [];
				
				for (let i = 0; i < lines.length; i++) {
					const line = lines[i];
					const isListItem = /^(\*|\-|\d+\.)\s/.test(line);
					
					if (isListItem) {
						if (!inList) {
							result.push('<ul>');
							inList = true;
						}
						const content = line.replace(/^(\*|\-|\d+\.)\s/, '');
						result.push(`<li>${content}</li>`);
					} else {
						if (inList) {
							result.push('</ul>');
							inList = false;
						}
						result.push(line);
					}
				}
				
				if (inList) {
					result.push('</ul>');
				}
				
				html = result.join('\n');
				
				// 换行
				html = html.replace(/\n/g, '<br>');
				
				return html;
			},
			
			// 拉取主题列表
			async fetchSubjects() {
				this.subjectsLoading = true;
				try {
					const res = await fetch(`${this.backendBase}/get_subject`);
					if (!res.ok) throw new Error(`HTTP ${res.status}`);
					this.subjects = await res.json();
				} catch (e) {
					console.error('获取主题失败', e);
				} finally {
					this.subjectsLoading = false;
				}
			},

			// 打开主题并加载历史消息
			async openSubject(subjectId) {
				if (this.isStreaming) this.cancelStream();
				this.currentSubjectId = subjectId;
				this.arr = [];
				try {
					const url = `${this.backendBase}/get_chatcontent_at_subjectid?subjectid=${subjectId}`;
					const res = await fetch(url);
					if (!res.ok) throw new Error(`HTTP ${res.status}`);
					const list = await res.json();
					// 将历史记录渲染到 arr
					for (const row of list) {
						// 解析附件标记，格式：[附件] URL
						let text = row.content || '';
						let isAttachment = false;
						let attachUrl = '';
						const m = text.match(/\[附件\]\s+(\S+)/);
						if (m && m[1]) {
							isAttachment = true;
							attachUrl = m[1].startsWith('/static/') ? `${this.backendBase}${m[1]}` : m[1];
							text = text.replace(/\n?\[附件\]\s+\S+/, '').trim();
						}
						this.arr.push({
							flag: row.role === 'assistant' ? 1 : 4,
							touxiang: row.role === 'assistant' ? "/static/touxiang/agent.png" : "/static/touxiang/touxiang.png",
							text,
							attachUrl,
							isAttachment
						});
					}
					this.scrollToBottom();
				} catch (e) {
					console.error('获取历史消息失败', e);
				}
			},

			// 侧边栏主题项：滑动交互
			subjectTouchStart(e, id) {
				this.subjectTouchStartX = e.touches && e.touches.length ? e.touches[0].pageX : e.changedTouches[0].pageX;
			},
			subjectTouchMove(e, id) {
				const currentX = e.touches && e.touches.length ? e.touches[0].pageX : e.changedTouches[0].pageX;
				const moveX = currentX - this.subjectTouchStartX;
				let target = Math.min(0, Math.max(-this.deleteWidth, moveX));
				this.$set(this.subjectSwipeX, id, target);
			},
			subjectTouchEnd(e, id) {
				const endX = e.changedTouches && e.changedTouches.length ? e.changedTouches[0].pageX : (e.touches && e.touches.length ? e.touches[0].pageX : 0);
				const distance = endX - this.subjectTouchStartX;
				const finalX = distance < -20 ? -this.deleteWidth : 0; // 阈值约 -20px
				this.$set(this.subjectSwipeX, id, finalX);
			},

			// 删除主题
			async confirmDeleteSubject(id) {
				try {
					// 简单确认，可替换为弹窗组件
					const ok = true;
					if (!ok) return;
					const res = await fetch(`${this.backendBase}/subject/${id}`, { method: 'DELETE' });
					if (!res.ok) throw new Error(`HTTP ${res.status}`);
					// 若删除的是当前会话，则清空窗口并重置 subjectId
					if (id === this.currentSubjectId) {
						this.currentSubjectId = 0;
						this.arr = [];
					}
					await this.fetchSubjects();
				} catch (e) {
					console.error('删除主题失败', e);
				}
			},

			// 对话消息实现（接入后端流式）
			async sendMessage() {
				const text = this.inputValue ? this.inputValue.trim() : '';
				if (!text || this.isStreaming) return;

				// 将附件合并到文本（仅作为上下文发送，不入库结构区分）
				let finalText = text;
				if (this.hasAttachment && this.attachmentUrl) {
					finalText = `${text}\n\n[附件] ${this.attachmentUrl}`;
				}

				// 添加用户消息
				this.arr.push({
					flag: 4,
					touxiang: "/static/touxiang/touxiang.png",
					text: finalText
				});

				// 清空输入框并滚动
				this.inputValue = "";
				this.scrollToBottom();

				try {
					await this.startStream(finalText);
				} catch (err) {
					console.error('流式请求失败', err);
					this.arr.push({
						flag: 1,
						touxiang: "/static/touxiang/agent.png",
						text: "抱歉，服务暂时不可用，请稍后再试"
					});
				} finally {
					this.isStreaming = false;
					this.abortController = null;
					// 发送完毕重置附件状态
					this.hasAttachment = false;
					this.attachmentUrl = '';
					this.scrollToBottom();
				}
			},

			// 选择并上传附件（图片或文件）
			async pickAndUpload() {
				try {
					// H5：用 input[type=file]
					if (typeof document !== 'undefined') {
						const file = await new Promise((resolve) => {
							const input = document.createElement('input');
							input.type = 'file';
							input.accept = 'image/*,application/pdf,application/zip,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document';
							input.onchange = () => resolve(input.files && input.files[0]);
							input.click();
						});
						if (!file) return;
						const form = new FormData();
						form.append('img1', file);
						const res = await fetch(`${this.backendBase}/upload`, { method: 'POST', body: form });
						if (!res.ok) throw new Error(`HTTP ${res.status}`);
						const data = await res.json();
						// 后端返回形如 /static/xxx，补全为可访问的绝对地址
						this.attachmentUrl = data.img ? `${this.backendBase}${data.img}` : '';
						this.hasAttachment = !!this.attachmentUrl;
						return;
					}

					// 其他端：使用 uni.chooseImage + uni.uploadFile
					const chooseRes = await uni.chooseImage({ count: 1 });
					if (!chooseRes || !chooseRes.tempFilePaths || !chooseRes.tempFilePaths[0]) return;
					const filePath = chooseRes.tempFilePaths[0];
					const uploadRes = await new Promise((resolve, reject) => {
						uni.uploadFile({
							url: `${this.backendBase}/upload`,
							filePath,
							name: 'img1',
							success: (res) => resolve(res),
							fail: reject
						});
					});
					let dataObj = {};
					try { dataObj = JSON.parse(uploadRes.data); } catch(_) {}
					this.attachmentUrl = dataObj.img ? `${this.backendBase}${dataObj.img}` : '';
					this.hasAttachment = !!this.attachmentUrl;
				} catch (e) {
					console.error('附件上传失败', e);
					this.hasAttachment = false;
					this.attachmentUrl = '';
				}
			},

			// 启动与读取后端流
			async startStream(userText) {
				// H5 环境：使用 fetch 流式读取
				if (typeof window !== 'undefined' && typeof window.fetch === 'function') {
					const url = `${this.backendBase}/stream`;
					this.abortController = new AbortController();
					this.isStreaming = true;

					// AI 占位消息
					const aiMsg = { flag: 1, touxiang: "/static/touxiang/agent.png", text: "" };
					this.arr.push(aiMsg);
					this.scrollToBottom();

					const res = await fetch(url, {
						method: 'POST',
						signal: this.abortController.signal,
						headers: { 
							'Accept': 'text/plain',
							'Content-Type': 'application/json'
						},
						body: JSON.stringify({
							text: userText,
							subjectid: this.currentSubjectId || 0,
							identity_id: this.currentIdentityId
						})
					});
					if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

					const reader = res.body.getReader();
					const decoder = new TextDecoder('utf-8');
					let received = '';
					let gotSubjectId = false;

					while (true) {
						const { value, done } = await reader.read();
						if (done) break;
						received += decoder.decode(value, { stream: true });

						// 首段为 subjectid
						if (!gotSubjectId) {
							const firstChunk = received.trim();
							const maybeId = parseInt(firstChunk, 10);
							if (!Number.isNaN(maybeId)) {
								this.currentSubjectId = maybeId;
								// 新建会话后刷新侧边栏并高亮
								this.fetchSubjects();
								gotSubjectId = true;
								received = '';
								continue;
							}
							const match = firstChunk.match(/^(\d+)/);
							if (match) {
								this.currentSubjectId = parseInt(match[1], 10);
								this.fetchSubjects();
								gotSubjectId = true;
								received = firstChunk.slice(match[1].length);
							}
						}

						if (received) {
							aiMsg.text += received;
							received = '';
							this.scrollToBottom();
						}
					}

					// 结束读取
 					await reader.cancel().catch(() => {});
					// 流式结束后自动刷新一次当前主题的历史，确保附件/图片等完整渲染
					if (this.currentSubjectId) {
						try { await this.openSubject(this.currentSubjectId); } catch(_) {}
					}
					return;
				}

				// 非 H5 环境：退化为一次性请求
				const url = `${this.backendBase}/chat`;
				uni.request({
					url,
					method: 'POST',
					data: {
						text: userText
					},
					header: {
						'Content-Type': 'application/json'
					},
					success: (res) => {
						const content = (res && res.data && res.data.content) ? res.data.content : '';
						this.arr.push({ flag: 1, touxiang: "/static/touxiang/agent.png", text: content || '（无响应）' });
					},
					fail: (err) => {
						console.error(err);
						this.arr.push({ flag: 1, touxiang: "/static/touxiang/agent.png", text: '请求失败' });
					}
				});
			},

			// 取消当前流
			cancelStream() {
				if (this.abortController) {
					try { this.abortController.abort(); } catch(e) {}
				}
				this.isStreaming = false;
				this.abortController = null;
			},

			// 滚动到底部
			scrollToBottom() {
				// 等待DOM更新（消息渲染完成）
				this.$nextTick(() => {
					const lastIndex = this.arr.length - 1;
					this.scrollToViewId = '';
					this.$nextTick(() => {
						this.scrollToViewId = `msg-${lastIndex}`;
					});
				});
			},

			// 新建对话功能
			MessagesPlus() {
				// 取消进行中的流
				if (this.isStreaming) {
					this.cancelStream();
				}
				// 将 subjectid 复位为 0，下一条消息将创建新主题
				this.currentSubjectId = 0;
				// 清空当前会话 UI，并放入一条提示
				this.arr = [];
				this.inputValue = '';
				this.arr.push({
					flag: 1,
					touxiang: "/static/touxiang/agent.png",
					text: "已新建对话"
				});
				this.scrollToBottom();
			},

			// 左侧抽屉相关实现
			touchStart(e) {
				this.startX = e.changedTouches[0].clientX;
				this.touching = true;
			},
			touchMove(e) {
				if (!this.touching) return;

				let moveX = e.touches[0].clientX - this.startX;

				if (!this.showSidebar && moveX < 0) return;
				// 初始界面左滑不触发
				if (!this.showSidebar && moveX > this.maxOffset) moveX = this.maxOffset;

				if (this.showSidebar && moveX < 0) {
					// 抽屉打开时，左滑跟随手指
					this.offsetX = this.maxOffset + moveX; // moveX 为负数
					this.offsetX = Math.max(0, this.offsetX); // 防止超出左边界
					return;
				}

				if (!this.showSidebar && moveX > 0) {
					// 初始界面右滑打开
					this.offsetX = Math.min(moveX, this.maxOffset);
				}
			},
			touchEnd(e) {
				this.touching = false;
				let distance = e.changedTouches[0].clientX - this.startX;

				if (!this.showSidebar && distance > 80) {
					this.openSidebar();
				} else if (this.showSidebar && distance < -80) {
					this.hideSidebar();
				} else {
					// 回弹到当前状态
					this.offsetX = this.showSidebar ? this.maxOffset : 0;
				}

			},
			openSidebar() {
				this.showSidebar = true;
				this.offsetX = this.maxOffset;
			},
			hideSidebar() {
				this.showSidebar = false;
				this.offsetX = 0;
			},

			// 打开链接
			openLink(url) {
				if (!url) return;
				this.previewUrl = url;
				this.previewVisible = true;
			},
			closePreview() { this.previewVisible = false; this.previewUrl = ''; },
		}
	}
</script>

<style scoped>
	/* 全局样式 */
	page {
		height: 100%;
		overflow-x: hidden;
		/* 禁止左右超出页面 */
		overflow-y: hidden;
		/* 保持和原来一样不滚动页面 */
		touch-action: pan-x;
		/* 允许水平滑动手势 */
	}

	.container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
		background: #f8f8f8;
	}

	/* 导航栏容器：固定定位 + 适配状态栏 */
	.nav-bar {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		z-index: 101;
		background-color: #ffffff;
		/* 正常状态背景 */
		box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
		/* 阴影放在 nav-bar 上，方便 dim 时移除 */
		transition: background-color 0.25s, box-shadow 0.25s, opacity 0.25s;
	}

	/* 导航内容区域 */
	.nav-content {
		height: 88rpx;
		background: transparent;
		/* 关键：改为透明，让 nav-bar 背景显现 */
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 30rpx;
	}

	/* 中间标题 */
	.nav-title {
		font-size: 34rpx;
		font-weight: bold;
		color: #333;
		flex: 1;
		text-align: center;
		/* 确保文字居中 */
	}

	/* 图标按钮外层容器（可点击区域） */
	.nav-btn {
		width: 60rpx;
		height: 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* 图标本身：控制显示大小 */
	.icon {
		width: 40rpx;
		height: 40rpx;
		/* object-fit 在小程序中不支持，所以靠 mode="aspectFit" 保证比例 */
	}

	/* 消息样式 */
	.message-list {
		flex: 1;
		padding: 20rpx;
		background: #f5f5f5;
		box-sizing: border-box;
	}

	.msg {
		max-width: 70%;
		padding: 14rpx 20rpx;
		border-radius: 12rpx;
		margin: 0rpx 0;
		word-break: break-word;
	}

	.msg-left {
		align-self: flex-start;
		background: #fff;
	}

	.msg-right {
		align-self: flex-end;
		background: #4facfe;
		color: #fff;
	}

	.chat-page {
		display: flex;
		flex-direction: column;
		flex: 1;
		/* 占据剩余空间 */
		position: relative;
		/* 重要：为 input-bar fixed 定位提供参考 */
		overflow: hidden;
		/* 防止溢出 */
	}

	.input {
		flex: 1;
		border: 2px solid #ddd;
		border-radius: 8rpx;
		padding: 0 20rpx;
		/* 输入框高度 */
		height: 82rpx;
	}

	.input-bar {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		display: flex;
		padding: 15rpx;
		border-top: 1px solid #ddd;
		background: #fff;
		z-index: 100;
		box-sizing: border-box;
	}

	.send-btn {
		margin-left: 0rpx;
		background: #4facfe;
		color: #fff;
		border-radius: 8rpx;
	}

	/* 历史页面 */
	/* 蒙层 */
	.overlay {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.4);
		z-index: 98;
	}

	/* 左侧抽屉 */
	.sidebar {
		position: fixed;
		top: 0;
		left: -70%;
		/* 初始隐藏 */
		width: 70%;
		height: 100%;
		background: #fff;
		z-index: 102;
		display: flex;
		flex-direction: column;
	}

	.sidebar-active {
		left: 0;
		/* 显示 */
	}

	.sidebar-header {
		height: 90rpx;
		font-size: 55rpx;
		font-weight: bold;
		display: flex;
		align-items: center;
		padding: 0 20rpx;
		border-bottom: 5px solid #000000;
	}

	.sidebar-list {
		flex: 1;
		padding: 10rpx;
		overflow-y: auto;
		/* 自定义滚动条样式 */
		scrollbar-width: thin;
		scrollbar-color: #c0c0c0 #f0f0f0;
	}
	
	/* Webkit浏览器滚动条样式 */
	.sidebar-list::-webkit-scrollbar {
		width: 8px;
	}
	
	.sidebar-list::-webkit-scrollbar-track {
		background: #f0f0f0;
		border-radius: 4px;
	}
	
	.sidebar-list::-webkit-scrollbar-thumb {
		background: #c0c0c0;
		border-radius: 4px;
	}
	
	.sidebar-list::-webkit-scrollbar-thumb:hover {
		background: #a0a0a0;
	}

	.sidebar-item {
		padding: 0;
		width: 510rpx;
		height: 40px; /* 固定条目高度，与内容/按钮对齐 */
		border-bottom: 2px solid #a8a8a8;
		position: relative;
		overflow: hidden;
		background: #fff; /* 确保背景统一 */
	}

	.sidebar-item.active {
		background: #eef5ff;
		color: #2b6cff;
		font-weight: 600;
	}

	.subject-swipe {
		position: relative; /* 内容层 */
		z-index: 2; /* 在按钮之上 */
		transition: transform 0.18s ease;
		will-change: transform;
		background: #fff;
		display: flex;
		align-items: center;
		width: 100%;
		height: 100%; /* 跟随父容器，确保与删除按钮等高 */
	}

	.subject-title {
		display: block;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		line-height: 44px; /* 与条目高度一致，垂直居中 */
		padding: 0 12px; /* 仅左右内边距 */
		flex: 1; /* 让标题占据剩余空间 */
	}

	.subject-delete {
		position: absolute;
		right: 0;
		top: 0;
		bottom: 0;
		width: 60px; /* 与 deleteWidth 保持一致 */
		display: flex;
		align-items: center;
		justify-content: center;
		background: #ff5b57; /* 微信风格红色 */
		z-index: 1; /* 在内容层下方，被覆盖，左移时显露 */
		opacity: 0; /* 初始隐藏 */
		transition: opacity 0.18s ease;
	}

	/* 左移超过一定阈值时，让按钮淡入 */
	.sidebar-item.swiping .subject-delete {
		opacity: 1;
	}

	.delete-icon {
		width: 32rpx;
		height: 32rpx;
		filter: brightness(0) invert(1); /* 白色icon */
	}

	/* 对话消息部分 */
	.chat-container {
		flex: 1;
		background: #fff7d5;
		overflow-y: auto;
		padding: 20rpx;
		box-sizing: border-box;
	}

	.chat-item {
		display: flex;
		margin-bottom: 20px;
	}

	.chat-item.ai {
		flex-direction: row;
		/* AI在左侧 */
	}

	.chat-item.user {
		flex-direction: row-reverse;
		/* text-align: right; */
		/* 用户在右侧 */
	}

	.avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		flex-shrink: 0;
		object-fit: cover;
	}

	/* AI头像背景色和大小 */
	.chat-item.ai .avatar {
		background-color: #e0e0e0;
		width: 40px;
		height: 40px;
	}

	.content {
		max-width: 70%;
		margin: 0 10px;
	}

	/* AI 消息框 */
	.chat-item.ai .content {
		max-width: 90%;
		margin-right: 5px;
		margin-left: 10px;
	}

	/* 用户消息框 */
	.chat-item.user .content {
		max-width: 90%;
		margin-left: 5px;
		margin-right: 10px;
	}

	.text-msg {
		padding: 8px 12px;
		border-radius: 8px;
		background-color: #f0f0f0;
		font-size: 14px;
		line-height: 1.4;
	}

	.chat-item.user .text-msg {
		background-color: #dddddd;
	}

	/* Markdown 样式 */
	.markdown-content {
		line-height: 1.4;
		font-size: 14px;
	}

	.markdown-content h1 {
		font-size: 1.3em;
		font-weight: bold;
		margin: 8px 0 6px 0;
		color: #333;
	}

	.markdown-content h2 {
		font-size: 1.2em;
		font-weight: bold;
		margin: 6px 0 4px 0;
		color: #444;
	}

	.markdown-content h3 {
		font-size: 1.1em;
		font-weight: bold;
		margin: 4px 0 2px 0;
		color: #555;
	}

	.markdown-content strong {
		font-weight: bold;
		color: #333;
	}

	.markdown-content em {
		font-style: italic;
		color: #666;
	}

	.markdown-content code {
		background-color: #f5f5f5;
		padding: 2px 4px;
		border-radius: 3px;
		font-family: 'Courier New', monospace;
		font-size: 0.85em;
		color: #d63384;
	}

	.markdown-content pre {
		background-color: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 6px;
		padding: 12px;
		margin: 8px 0;
		overflow-x: auto;
	}

	.markdown-content pre code {
		background-color: transparent;
		padding: 0;
		color: #333;
	}

	.markdown-content a {
		color: #007bff;
		text-decoration: none;
	}

	.markdown-content a:hover {
		text-decoration: underline;
	}

	.markdown-content ul {
		margin-top: 2px;     /* 只调整顶部间距 */
    	margin-bottom: 2px;  /* 只调整底部间距 */
		padding-left: 5px;
	}

	.markdown-content li {
		margin: 2px 0;
		list-style-type: disc;
	}

	.img-msg {
		width: 150px;
		height: 100px;
		border-radius: 8px;
	}

	.video-msg {
		width: 200px;
		height: 120px;
		border-radius: 8px;
	}

	/* 附件预览样式 */
	.attach-block {
		display: flex;
		align-items: center;
		margin-top: 6px;
		padding: 8px 12px;
		background-color: #e0e0e0;
		border-radius: 8px;
	}

	.attach-block .img-msg {
		width: 40px;
		height: 40px;
		margin-right: 10px;
	}

	.attach-block .link-msg {
		text-decoration: underline;
		word-break: break-all;
		margin-top: 6px;
	}

	.upload-btn {
		width: 46px;
		height: 46px;
		margin: 0 0px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
		background:rgb(255, 255, 255);
		transition: background-color 0.2s ease;
	}

	.upload-btn.uploaded {
		background: #2cfff8;
	}

	.upload-icon {
		width: 32px; /* 图标尺寸 */
		height: 32px;
		object-fit: contain; /* 保持比例显示在容器内 */
	}

	/* 预览弹窗样式 */
	.preview-mask {
		position: fixed;
		left: 0; right: 0; top: 0; bottom: 0;
		background: rgba(0,0,0,0.5);
		z-index: 999;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.preview-dialog {
		width: 80vw;
		max-width: 640px;
		background: #fff;
		border-radius: 10px;
		overflow: hidden;
		box-shadow: 0 8px 24px rgba(0,0,0,0.25);
	}

	.preview-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px 12px;
		border-bottom: 1px solid #eee;
	}

	.preview-title { font-weight: 600; }

	.preview-close {
		width: 28px;
		height: 28px;
		line-height: 28px;
		text-align: center;
		font-size: 20px;
		border-radius: 50%;
		background: #f3f3f3;
	}

	.preview-body {
		padding: 12px;
		max-height: 70vh;
		overflow: auto;
	}

	.preview-image {
		width: 100%;
		height: auto;
		max-height: 60vh; /* 防止过高溢出 */
		border-radius: 6px;
		background: #fafafa;
	}

	.preview-link {
		color: #2b6cff;
		text-decoration: underline;
		word-break: break-all;
	}

	.img-thumb {
		width: 120px;
		height: 90px;
		border-radius: 8px;
		object-fit: cover;
		background: #f2f2f2;
		cursor: pointer;
	}

	/* 侧边栏右下角刷新按钮 */
	.sidebar-refresh-btn {
		position: absolute;
		bottom: 30rpx;
		right: 30rpx;
		width: 60rpx;
		height: 60rpx;
		background: rgba(222, 222, 222, 0.8);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
		z-index: 10;
		transition: all 0.3s ease;
	}

	.sidebar-refresh-btn:active {
		transform: scale(0.9);
		background: rgba(180, 180, 180, 0.9);
	}

	.sidebar-refresh-btn image {
		width: 35rpx;
		height: 35rpx;
		filter: brightness(0) invert(0.3); /* 深灰色图标 */
	}

	.sidebar-refresh-btn.rotating {
		background: #afccf7;
		box-shadow: 0 2rpx 8rpx rgba(150, 200, 150, 0.3);
	}

	.sidebar-refresh-btn.rotating image {
		animation: rotate 1s linear infinite;
	}

	@keyframes rotate {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	/* 自定义Toast样式 */
	.custom-toast {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 9999;
		pointer-events: none;
	}

	.toast-content {
		background: rgba(0, 0, 0, 0.8);
		border-radius: 12rpx;
		padding: 24rpx 40rpx;
		min-width: 300rpx;
		max-width: 600rpx;
		text-align: center;
		box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.3);
	}

	.toast-content.success {
		background: rgba(0, 0, 0, 0.8);
	}

	.toast-content.error {
		background: rgba(220, 53, 69, 0.9);
	}

	.toast-text {
		color: white;
		font-size: 28rpx;
		line-height: 1.4;
		word-break: break-all;
	}

	/* 思考块样式 - 使用更高优先级的选择器 */
	.markdown-content .thinking-block,
	.markdown-content div.thinking-block,
	.thinking-block {
		background-color: #ffffff !important;
		border: 2px solid #666666 !important;
		border-left: 6px solid #666666 !important;
		padding: 20rpx !important;
		color: #999999 !important;
		font-weight: 600 !important;
		border-radius: 12rpx !important;
		margin: 16rpx 0 !important;
		font-size: 26rpx !important;
		line-height: 1.8 !important;
		font-style: italic !important;
		box-shadow: 0 4rpx 8rpx rgba(0, 123, 255, 0.2) !important;
		position: relative !important;
		display: block !important;
		background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%) !important;
	}
	
	.markdown-content .thinking-block::before {
		content: "💭" !important;
		position: absolute !important;
		left: 8rpx !important;
		top: 8rpx !important;
		font-size: 20rpx !important;
		opacity: 0.6 !important;
	}
	
	.markdown-content .thinking-block {
		padding-left: 40rpx !important;
	}
</style>