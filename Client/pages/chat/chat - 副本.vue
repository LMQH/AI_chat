<template>
	<view class="container" @touchstart="touchStart" @touchmove="touchMove" @touchend="touchEnd">

		<!-- 自定义导航栏 -->
		<view class="nav-bar" :style="{ 
			        paddingTop: statusBarHeight + 'px', 
			        transform: 'translateX(' + offsetX + 'px)', 
			        backgroundColor: 'rgba(230,230,230,' + navOpacity + ')'
			    }" >

			<view class="nav-content" :class="{ 'nav-dim': showSidebar }">
				<!-- 左侧图标按钮 -->
				<view class="nav-btn">
					<image @click="openSidebar" src="/static/icons/chat-line-round.png" mode="aspectFit" class="icon">
					</image>
				</view>

				<!-- 中间标题 -->
				<view class="nav-title">AI</view>

				<!-- 右侧图标按钮 -->
				<view class="nav-btn">
					<image src="/static/icons/circle-plus.png" mode="aspectFit" class="icon"></image>
				</view>
			</view>
		</view>

		<!-- 聊天页面 -->
		<view class="chat-page">
			<!-- 底部输入框 -->
			<view class="input-bar">
				<input class="input" v-model="inputValue" placeholder="输入消息..." />
				<button class="send-btn" @click="sendMessage">发送</button>
			</view>

			<!-- 对话消息 -->
			<scroll-view class="chat-container" scroll-y :scroll-with-animation="true" enable-back-to-top
				:scroll-into-view="scrollToViewId" :style="{
				paddingTop: (statusBarHeight + navContentHeight) + 'px', // 避开导航栏
				paddingBottom: inputBarHeight + 'px', // 避开输入框
				paddingTop: (statusBarHeight * 2 + navContentHeight * 2 + 30) + 'rpx', 
				paddingBottom: (inputBarHeight * 2 + 30) + 'rpx',
				// padding: 20rpx 20rpx 20rpx 20rpx,  // 保留左右下内边距，不影响其他方向
				}">
				<view v-for="(item, index) in arr" :key="index" :id="'msg-' + index"
					:class="['chat-item', item.flag <= 3 ? 'ai' : 'user']">
					<image class="avatar" :src="item.touxiang" mode="aspectFill"></image>
					<view class="content">
						<!-- 文本 -->
						<view v-if="item.flag === 1 || item.flag === 4" class="text-msg">{{ item.text }}</view>
						<!-- 图片 -->
						<image v-else-if="item.flag === 2 || item.flag === 5" :src="item.img" class="img-msg">
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
			:style="{ backgroundColor: 'rgba(0,0,0,' + (0.4 * offsetX/maxOffset) + ')' }" @click="hideSidebar"></view>

		<!-- 左侧菜单 -->
		<view class="sidebar" :style="{ left: (-70* (1 - offsetX/maxOffset)) + '%' }">
			<view class="sidebar-header">示例聊天记录</view>
			<scroll-view scroll-y class="sidebar-list">
				<view v-for="(msg, index) in messages" :key="'side'+index" class="sidebar-item">
					<text>{{ msg.from }}: {{ msg.text }}</text>
				</view>
			</scroll-view>
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
				messages: [{
						from: 'you',
						text: '你好，我是AI助手'
					},
					{
						from: 'me',
						text: '很高兴见到你！'
					}
				],
				arr: [{
					flag: 1, // AI文本消息
					touxiang: "/static/touxiang/logo.png", // 假设这是AI头像
					text: "欢迎使用AI助手"
				}],
				// 固定高度常量（rpx转px需乘以2，因uni-app默认rpx基于750宽屏）
				navContentHeight: 44, // nav-content高度88rpx = 44px（750屏1rpx=0.5px）
				inputBarHeight: 56, // input-bar总高度：82rpx(input) + 30rpx(padding) = 112rpx = 56px
				scrollToViewId: '' // 滚动锚点ID，用于scroll-view原生滚动
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
				}
			})
		},
		computed: {
			navOpacity() {
				return 1 - this.offsetX / this.maxOffset * 0.5; // 最大半透明灰度
			}
		},
		methods: {
			// 对话消息实现
			sendMessage() {
				const text = this.inputValue?.trim();
				if (!text) return;

				// 添加用户消息
				this.arr.push({
					flag: 4,
					touxiang: "/static/touxiang/logo.png",
					text: text
				});

				// 清空输入框
				this.inputValue = "";

				// 发送后滚动
				this.scrollToBottom();

				// 模拟 AI 回复
				setTimeout(() => {
					this.arr.push({
						flag: 1,
						touxiang: "/static/touxiang/logo.png",
						text: "这是AI的回复"
					});
					this.scrollToBottom(); //滚动
				}, 500);
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
			}
		}
	}
</script>

<style scoped>
	/* 全局样式，防止页面本身滚动 */
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

	/* 菜单出来时导航栏变灰 */
	.nav-bar.nav-bar-dim {
		background-color: #e6e6e6;
		box-shadow: none;
		/* 去掉阴影使“灰化”更明显 */
	}

	.nav-bar.nav-bar-dim .nav-title {
		color: #666;
	}

	.nav-bar.nav-bar-dim .icon {
		opacity: 0.8;
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
		margin-left: 14rpx;
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
		height: 100rpx;
		font-size: 34rpx;
		display: flex;
		align-items: center;
		padding: 0 20rpx;
		border-bottom: 1px solid #eee;
	}

	.sidebar-list {
		flex: 1;
		padding: 10rpx;
	}

	.sidebar-item {
		padding: 14rpx;
		border-bottom: 1px solid #f0f0f0;
	}

	/* 对话消息部分 */
	.chat-container {
		flex: 1;
		background: #fff7d5;
		overflow-y: auto;
		padding: 20rpx;
		box-sizing: border-box;
		height: 100%;
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
	}

	.content {
		max-width: 70%;
		margin: 0 10px;
	}

	.text-msg {
		padding: 8px 12px;
		border-radius: 8px;
		background-color: #f0f0f0;
	}

	.chat-item.user .text-msg {
		background-color: #a0e75a;
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
</style>