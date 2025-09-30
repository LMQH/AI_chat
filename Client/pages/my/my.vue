<template>
	<view>
		<image class="logo" src="/static/logo.png" mode=""></image>
		<view class="box1">
			my
		</view>
		<view class="box2">
			111
		</view>

	</view>
</template>

<script>
	export default {
		data() {
			return {

			}
		},
		methods: {

		}
	}
</script>

<style>
	.logo {
		height: 100rpx;
		width: 100rpx;
		margin-top: 0rpx;
		margin-left: 325rpx;
		margin-right: auto;
		margin-bottom: auto;
	}

	.box1 {
		width: 750rpx;
		height: 100rpx;
		background-color: aquamarine;
	}

	.box2 {
		width: 750rpx;
		height: 100rpx;
		background-color: greenyellow;
	}

	.navbar {
		width: 750rpx;
		margin-top: 20rpx;
		display: flex;
		justify-content: flex-start;
		flex-wrap: wrap;
	}

	.navbar .btn {
		width: 120rpx;
		height: 140rpx;
		margin-left: 3rpx;
		margin-top: 10rpx;

	}

	.navbar .nav_img {
		width: 60rpx;
		height: 60rpx;
		margin-left: 30rpx;
	}
</style>